from __future__ import annotations
from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id     = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash  = Column(Text, nullable=False)
    expires_at  = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at  = Column(TIMESTAMP(timezone=True), nullable=False, server_default="now()")

    user = relationship("User", back_populates="refresh_tokens")
