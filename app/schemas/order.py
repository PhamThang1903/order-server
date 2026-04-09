from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.schemas.order_item import OrderItemResponse

class OrderBase(BaseModel):
    platform_id: UUID
    order_code: str
    customer_id: UUID | None = None
    total_amount: Decimal = Decimal("0")
    note_internal: str | None = None
    customer_phone: str | None = None
    tracking_url: str | None = None
    tracking_provider: str | None = None

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: str | None = None
    note_internal: str | None = None
    customer_phone: str | None = None
    tracking_url: str | None = None
    tracking_provider: str | None = None
    current_location: str | None = None
    shipper_phone: str | None = None
    extracted_text: str | None = None
    total_amount: Decimal | None = None

class OrderResponse(BaseModel):
    id: UUID
    platform_id: UUID
    order_code: str
    customer_id: UUID | None
    status: str
    total_amount: Decimal
    customer_phone: str | None
    tracking_url: str | None
    tracking_provider: str | None
    current_location: str | None
    last_tracked_at: datetime | None
    attached_image_url: str | None
    extracted_text: str | None
    created_at: datetime
    updated_at: datetime
    updated_by: UUID | None
    items: list[OrderItemResponse]

    # Admin-only fields — set to None before returning to customer
    note_internal: str | None = None
    shipper_phone: str | None = None

    model_config = ConfigDict(from_attributes=True)

class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    limit: int
