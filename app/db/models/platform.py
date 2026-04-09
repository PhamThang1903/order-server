from __future__ import annotations
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base

class Platform(Base):
    __tablename__ = "platforms"

    id      = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name    = Column(String(20), unique=True, nullable=False)  # 'shopee','lazada','tiktok','manual'
