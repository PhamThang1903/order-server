from __future__ import annotations
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.services import auth_service
from app.db.models.user import User

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    return await auth_service.login_with_firebase(db, request.firebase_id_token)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    return await auth_service.refresh_tokens(db, request.refresh_token)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await auth_service.logout_user(db, current_user.id)
    return None
