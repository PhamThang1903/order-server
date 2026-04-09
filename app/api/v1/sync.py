from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.dependencies import get_db, get_current_user
from app.db.models.order import Order
from app.db.models.status_history import StatusHistory
from app.db.models.user import User
from app.schemas.order import OrderResponse
from app.schemas.sync import SyncPushRequest, SyncPushResult, SyncPushItem
from app.services import fcm_service, order_service

router = APIRouter()

@router.post("/push", response_model=SyncPushResult)
async def sync_push(
    request: SyncPushRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    accepted = []
    conflicted = []
    
    for item in request.changes:
        # Use SELECT FOR UPDATE to avoid race conditions
        stmt = select(Order).where(Order.id == item.id).with_for_update()
        result = await db.execute(stmt)
        db_order = result.scalar_one_or_none()
        
        if not db_order:
             # If order doesn't exist on server, we might ignore or accept depending on policy
             # For now, only handle existing orders
             continue

        # Conflict check: Last-write-wins based on updated_at
        # If client's updated_at is OLDER than server, server wins.
        # We also need to check if the user has permission (customer can only push their own orders)
        if current_user.role == "customer" and db_order.customer_id != current_user.id:
             continue # Or silent ignore

        if item.updated_at < db_order.updated_at:
             # Conflict! Server is newer.
             order_resp = OrderResponse.model_validate(db_order)
             conflicted.append(order_service.apply_customer_mask(order_resp, current_user.role))
             
             # Notify Sync Conflict
             await fcm_service.notify_sync_conflict(db, current_user.id, db_order)
             
             # Log sync history
             history = StatusHistory(
                order_id=db_order.id,
                old_status=db_order.status,
                new_status=db_order.status, # No change, but log that server won
                changed_by=f"sync:{current_user.id}",
                source="sync"
             )
             db.add(history)
             continue
        
        # Accepted: Update server version
        old_status = db_order.status
        old_location = db_order.current_location
        
        update_data = item.model_dump(exclude_unset=True, exclude={"id", "updated_at"})
        status_changed = ("status" in update_data and update_data["status"] != old_status)
        location_changed = ("current_location" in update_data and update_data["current_location"] != old_location)
        
        for field, value in update_data.items():
            setattr(db_order, field, value)
            
        # ALWAYS set updated_at server-side to avoid clock skew
        db_order.updated_at = datetime.now(timezone.utc)
        db_order.updated_by = current_user.id
        
        if status_changed or location_changed:
             history = StatusHistory(
                order_id=db_order.id,
                old_status=old_status,
                new_status=db_order.status,
                old_location=old_location,
                new_location=db_order.current_location,
                changed_by=str(current_user.id),
                source="sync"
             )
             db.add(history)
             
        accepted.append(db_order.id)
        
    await db.commit()
    return SyncPushResult(accepted=accepted, conflicted=conflicted)

@router.get("/pull", response_model=list[OrderResponse])
async def sync_pull(
    since: datetime = Query(..., description="ISO 8601 timestamp"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Order).where(Order.updated_at > since)
    if current_user.role == "customer":
         stmt = stmt.where(Order.customer_id == current_user.id)
         
    result = await db.execute(stmt)
    orders = result.scalars().all()
    
    # Apply mask and validate
    masked_orders = []
    for order in orders:
         order_resp = OrderResponse.model_validate(order)
         masked_orders.append(order_service.apply_customer_mask(order_resp, current_user.role))
         
    return masked_orders
