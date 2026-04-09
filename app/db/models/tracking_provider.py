from __future__ import annotations
from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base

class TrackingProvider(Base):
    __tablename__ = "tracking_providers"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider            = Column(String(10), unique=True, nullable=False)
    base_url            = Column(Text, nullable=False)
    auth_header_key     = Column(Text, nullable=True)
    auth_header_value   = Column(Text, nullable=True)
    is_enabled          = Column(Boolean, nullable=False, default=True)
