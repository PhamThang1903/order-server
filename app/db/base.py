from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

# Sync engine (psycopg2)
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,  # Log SQL queries
    pool_pre_ping=True,
)

# Sync session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Base class for all models
class Base(DeclarativeBase):
    pass
