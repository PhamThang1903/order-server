from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_users(db: Session, role: str | None = None, is_active: bool | None = None):
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    return db.execute(stmt).scalars().all()


def create_user(db: Session, user_in: UserCreate, creator_id: UUID | None = None) -> User:
    stmt = select(User).where(User.email == user_in.email)
    if db.execute(stmt).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    db_user = User(**user_in.model_dump(), created_by=creator_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: UUID, user_in: UserUpdate) -> User:
    db_user = db.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def toggle_user_active(db: Session, user_id: UUID) -> User:
    db_user = db.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_user.is_active = not db_user.is_active
    db.commit()
    db.refresh(db_user)
    return db_user
