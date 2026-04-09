from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from decimal import Decimal

class OrderItemBase(BaseModel):
    product_name: str
    sku: str | None = None
    quantity: int
    unit_price: Decimal

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemUpdate(BaseModel):
    product_name: str | None = None
    sku: str | None = None
    quantity: int | None = None
    unit_price: Decimal | None = None

class OrderItemResponse(OrderItemBase):
    id: UUID
    order_id: UUID
    
    model_config = ConfigDict(from_attributes=True)
