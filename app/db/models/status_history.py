from __future__ import annotations
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base

class StatusHistory(Base):
    __tablename__ = "status_history"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id        = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    old_status      = Column(String(20), nullable=True)
    new_status      = Column(String(20), nullable=False)
    old_location    = Column(Text, nullable=True)
    new_location    = Column(Text, nullable=True)
    changed_by      = Column(String(100), nullable=False)   # user UUID string or 'system'
    changed_at      = Column(TIMESTAMP(timezone=True), nullable=False, server_default="now()")
    source          = Column(String(20), nullable=False) # 'manual' | 'auto_tracking' | 'sync'

    order = relationship("Order", back_populates="history")
