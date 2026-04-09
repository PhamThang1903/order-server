from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user, require_admin
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderListResponse
from app.services import order_service, storage_service
from app.db.models.user import User

router = APIRouter()

@router.post("/{order_id}/image", response_model=OrderResponse)
async def upload_order_attached_image(
    order_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch order
    order = await db.get(order_service.Order, order_id)
    if not order or order.is_deleted:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
         
    # 2. Upload to S3
    image_url = await storage_service.upload_order_image(file, str(order_id))
    
    # 3. Update DB
    order.attached_image_url = image_url
    order.updated_at = datetime.now(timezone.utc)
    order.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(order)
    
    order_resp = OrderResponse.model_validate(order)
    return order_service.apply_customer_mask(order_resp, current_user.role)

@router.get("/", response_model=OrderListResponse)
async def list_orders(
    platform_id: UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    orders, total = await order_service.get_orders(
        db, current_user, platform_id, status_filter, from_date, to_date, search, page, limit
    )
    
    # Apply customer mask
    masked_orders = []
    for order in orders:
        order_resp = OrderResponse.model_validate(order)
        masked_orders.append(order_service.apply_customer_mask(order_resp, current_user.role))
        
    return OrderListResponse(items=masked_orders, total=total, page=page, limit=limit)

@router.post("/", response_model=OrderResponse)
async def create_new_order(
    order_in: OrderCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    order = await order_service.create_order(db, order_in, current_user.id)
    return OrderResponse.model_validate(order)

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    order = await db.get(order_service.Order, order_id)
    if not order or order.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
    if current_user.role == "customer" and order.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
    order_resp = OrderResponse.model_validate(order)
    return order_service.apply_customer_mask(order_resp, current_user.role)

@router.patch("/{order_id}", response_model=OrderResponse)
async def update_existing_order(
    order_id: UUID,
    order_in: OrderUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    order = await order_service.update_order(db, order_id, order_in, current_user.id)
    return OrderResponse.model_validate(order)

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    await order_service.soft_delete_order(db, order_id, current_user.id)
    return None
