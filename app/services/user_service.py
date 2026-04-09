from __future__ import annotations
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate

async def get_users(db: AsyncSession, role: str | None = None, is_active: bool | None = None):
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    result = await db.execute(stmt)
    return result.scalars().all()

async def create_user(db: AsyncSession, user_in: UserCreate, creator_id: UUID | None = None) -> User:
    # Check if exists
    stmt = select(User).where(User.email == user_in.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    db_user = User(
        **user_in.model_dump(),
        created_by=creator_id
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, user_id: UUID, user_in: UserUpdate) -> User:
    db_user = await db.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def toggle_user_active(db: AsyncSession, user_id: UUID) -> User:
    db_user = await db.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    db_user.is_active = not db_user.is_active
    await db.commit()
    await db.refresh(db_user)
    return db_user
