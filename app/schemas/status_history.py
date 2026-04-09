from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class StatusHistoryBase(BaseModel):
    order_id: UUID
    old_status: str | None = None
    new_status: str
    old_location: str | None = None
    new_location: str | None = None
    changed_by: str
    changed_at: datetime
    source: str # manual, auto_tracking, sync

class StatusHistoryResponse(StatusHistoryBase):
    id: UUID
    
    model_config = ConfigDict(from_attributes=True)
