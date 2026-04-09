from __future__ import annotations
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.schemas.order import OrderResponse

class SyncPushItem(BaseModel):
    id: UUID
    updated_at: datetime          # client-side timestamp for conflict check
    status: str | None = None
    current_location: str | None = None
    note_internal: str | None = None
    # ... other mutable fields as needed

class SyncPushRequest(BaseModel):
    changes: list[SyncPushItem]

class SyncPushResult(BaseModel):
    accepted: list[UUID]          # server accepted client version
    conflicted: list[OrderResponse]  # server version wins, client must update
