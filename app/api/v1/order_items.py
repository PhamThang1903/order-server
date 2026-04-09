from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, require_admin
from app.schemas.order_item import OrderItemCreate, OrderItemUpdate, OrderItemResponse
from app.db.models.order import Order
from app.db.models.order_item import OrderItem

router = APIRouter()

@router.post("/{order_id}/items", response_model=OrderItemResponse)
async def add_item(
    order_id: UUID,
    item_in: OrderItemCreate,
    current_admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    order = await db.get(Order, order_id)
    if not order or order.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
    db_item = OrderItem(
        **item_in.model_dump(),
        order_id=order_id
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

@router.patch("/items/{item_id}", response_model=OrderItemResponse)
async def update_item(
    item_id: UUID,
    item_in: OrderItemUpdate,
    current_admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    db_item = await db.get(OrderItem, item_id)
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        
    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
        
    await db.commit()
    await db.refresh(db_item)
    return db_item

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: UUID,
    current_admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    db_item = await db.get(OrderItem, item_id)
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        
    await db.delete(db_item)
    await db.commit()
    return None
