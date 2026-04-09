from __future__ import annotations
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Engine setup
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True, # Log SQL queries
    future=True,
)

# SessionLocal setup
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for all models
class Base(DeclarativeBase):
    pass
