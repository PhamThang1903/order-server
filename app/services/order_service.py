from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from fastapi import HTTPException, status
from decimal import Decimal
from app.db.models.order import Order
from app.db.models.order_item import OrderItem
from app.db.models.status_history import StatusHistory
from app.db.models.user import User
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse

async def get_orders(
    db: AsyncSession, 
    user: User,
    platform_id: UUID | None = None,
    status_filter: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 20
):
    stmt = select(Order).where(Order.is_deleted == False)
    
    if user.role == "customer":
        stmt = stmt.where(Order.customer_id == user.id)
    
    if platform_id:
        stmt = stmt.where(Order.platform_id == platform_id)
    if status_filter:
        stmt = stmt.where(Order.status == status_filter)
    if from_date:
        stmt = stmt.where(Order.created_at >= from_date)
    if to_date:
        stmt = stmt.where(Order.created_at <= to_date)
    if search:
        stmt = stmt.where(Order.order_code.ilike(f"%{search}%"))
        
    # Total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.execute(count_stmt)
    total_count = total.scalar_one() or 0
    
    # Pagination
    stmt = stmt.order_by(Order.updated_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(stmt)
    orders = result.scalars().all()
    
    return orders, total_count

async def create_order(db: AsyncSession, order_in: OrderCreate, creator_id: UUID) -> Order:
    db_order = Order(
        **order_in.model_dump(),
        updated_by=creator_id
    )
    db.add(db_order)
    await db.flush() # Get ID
    
    # Initial history
    history = StatusHistory(
        order_id=db_order.id,
        old_status=None,
        new_status=db_order.status,
        changed_by=str(creator_id),
        source="manual"
    )
    db.add(history)
    
    await db.commit()
    await db.refresh(db_order)
    return db_order

async def update_order(db: AsyncSession, order_id: UUID, order_in: OrderUpdate, updated_by_id: UUID) -> Order:
    stmt = select(Order).where(Order.id == order_id, Order.is_deleted == False)
    result = await db.execute(stmt)
    db_order = result.scalar_one_or_none()
    
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
    old_status = db_order.status
    old_location = db_order.current_location
    
    update_data = order_in.model_dump(exclude_unset=True)
    
    status_changed = ("status" in update_data and update_data["status"] != old_status)
    location_changed = ("current_location" in update_data and update_data["current_location"] != old_location)
    
    for field, value in update_data.items():
        setattr(db_order, field, value)
        
    db_order.updated_at = datetime.now(timezone.utc)
    db_order.updated_by = updated_by_id
    
    if status_changed or location_changed:
        history = StatusHistory(
            order_id=order_id,
            old_status=old_status,
            new_status=db_order.status,
            old_location=old_location,
            new_location=db_order.current_location,
            changed_by=str(updated_by_id),
            source="manual"
        )
        db.add(history)
        
        # FCM trigger
        from app.services import fcm_service
        await fcm_service.notify_status_or_location_changed(
            db, db_order, 
            db_order.status if status_changed else None,
            db_order.current_location if location_changed else None
        )
        
    await db.commit()
    await db.refresh(db_order)
    return db_order

async def soft_delete_order(db: AsyncSession, order_id: UUID, deleted_by_id: UUID):
    db_order = await db.get(Order, order_id)
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
    db_order.is_deleted = True
    db_order.updated_at = datetime.now(timezone.utc)
    db_order.updated_by = deleted_by_id
    
    await db.commit()

def apply_customer_mask(order: OrderResponse, role: str) -> OrderResponse:
    if role == "customer":
        order.note_internal = None
        order.shipper_phone = None
    return order
