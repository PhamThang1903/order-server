from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.dependencies import get_db, get_current_user, require_admin
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services import user_service
from app.db.models.user import User

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
def list_users(
    role: str | None = None,
    is_active: bool | None = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return user_service.get_users(db, role, is_active)


@router.post("/", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return user_service.create_user(db, user_in, current_user.id)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")
    return db.get(User, user_id)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")

    if current_user.role != "admin":
        user_in.role = None
        user_in.is_active = None

    return user_service.update_user(db, user_id, user_in)


@router.patch("/{user_id}/toggle-active", response_model=UserResponse)
def toggle_active(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return user_service.toggle_user_active(db, user_id)


@router.put("/{user_id}/fcm-token", response_model=UserResponse)
def update_fcm_token(
    user_id: UUID,
    fcm_token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")

    user_in = UserUpdate(fcm_token=fcm_token)
    return user_service.update_user(db, user_id, user_in)
