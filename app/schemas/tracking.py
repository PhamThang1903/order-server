from __future__ import annotations
from pydantic import BaseModel
from uuid import UUID

class TrackingResult(BaseModel):
    order_id: UUID
    is_changed: bool
    new_status: str | None = None
    new_location: str | None = None
    shipper_phone: str | None = None
    raw_data: dict | None = None
