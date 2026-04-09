from __future__ import annotations
from sqlalchemy import Column, String, Numeric, Boolean, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base

class Order(Base):
    __tablename__ = "orders"

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform_id          = Column(UUID(as_uuid=True), ForeignKey("platforms.id"), nullable=False)
    order_code           = Column(String(255), nullable=False)
    customer_id          = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status               = Column(String(20), nullable=False, default="pending")
    total_amount         = Column(Numeric(15, 2), nullable=False, default=0)
    note_internal        = Column(Text, nullable=True)
    customer_phone       = Column(String(20), nullable=True)
    tracking_url         = Column(Text, nullable=True)
    tracking_provider    = Column(String(10), nullable=True)
    current_location     = Column(Text, nullable=True)
    shipper_phone        = Column(String(20), nullable=True)
    last_tracked_at      = Column(TIMESTAMP(timezone=True), nullable=True)
    tracking_retry_count = Column(Integer, nullable=False, default=0)
    attached_image_url   = Column(Text, nullable=True)
    extracted_text       = Column(Text, nullable=True)
    created_at           = Column(TIMESTAMP(timezone=True), nullable=False, server_default="now()")
    updated_at           = Column(TIMESTAMP(timezone=True), nullable=False, server_default="now()")
    updated_by           = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_deleted           = Column(Boolean, nullable=False, default=False)

    platform       = relationship("Platform")
    customer       = relationship("User", foreign_keys=[customer_id])
    updated_by_user= relationship("User", foreign_keys=[updated_by])
    items          = relationship("OrderItem", back_populates="order",
                                  cascade="all, delete-orphan")
    history        = relationship("StatusHistory", back_populates="order",
                                  order_by="StatusHistory.changed_at.desc()")
