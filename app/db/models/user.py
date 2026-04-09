from __future__ import annotations
from sqlalchemy import Column, String, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid    = Column(String(128), unique=True, nullable=True)
    email           = Column(String(255), unique=True, nullable=False)
    name            = Column(String(255), nullable=False)
    role            = Column(String(20), nullable=False) # 'admin' | 'customer'
    created_by      = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    fcm_token       = Column(Text, nullable=True)
    is_active       = Column(Boolean, nullable=False, default=True)
    created_at      = Column(TIMESTAMP(timezone=True), nullable=False, server_default="now()")
    updated_at      = Column(TIMESTAMP(timezone=True), nullable=False, server_default="now()")

    creator = relationship("User", remote_side=[id])
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
