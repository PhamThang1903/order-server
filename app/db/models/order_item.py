from __future__ import annotations
from sqlalchemy import Column, String, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base

class OrderItem(Base):
    __tablename__ = "order_items"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id        = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_name    = Column(String(255), nullable=False)
    sku             = Column(String(100), nullable=True)
    quantity        = Column(Integer, nullable=False)
    unit_price      = Column(Numeric(15,2), nullable=False)

    order = relationship("Order", back_populates="items")
