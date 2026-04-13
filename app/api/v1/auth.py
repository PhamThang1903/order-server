from __future__ import annotations
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.services import auth_service
from app.db.models.user import User

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    return auth_service.login_with_firebase(db, request.firebase_id_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: RefreshRequest,
    db: Session = Depends(get_db),
):
    return auth_service.refresh_tokens(db, request.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    auth_service.logout_user(db, current_user.id)
    return None
