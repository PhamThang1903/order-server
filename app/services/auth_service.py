from __future__ import annotations
from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from fastapi import HTTPException, status
from firebase_admin import auth
from app.core.config import settings
from app.core.security import create_access_token, hash_refresh_token
from app.db.models.user import User
from app.db.models.refresh_token import RefreshToken
from app.schemas.auth import TokenResponse, RegisterRequest


def login_with_firebase(db: Session, firebase_id_token: str) -> TokenResponse:
    try:
        decoded_token = auth.verify_id_token(firebase_id_token)
        uid = decoded_token.get("uid")
        email = decoded_token.get("email")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase ID token")

    stmt = select(User).where((User.firebase_uid == uid) | (User.email == email))
    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not registered. Contact admin.")

    # Link firebase_uid if missing
    if not user.firebase_uid:
        user.firebase_uid = uid
        db.commit()

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    return _issue_tokens(db, user)


def register_with_firebase(db: Session, request: RegisterRequest) -> TokenResponse:
    try:
        decoded_token = auth.verify_id_token(request.firebase_id_token)
        uid = decoded_token.get("uid")
        token_email = decoded_token.get("email")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase ID token")

    # Safety: ensure email in token matches email in request
    if token_email and token_email != request.email:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email mismatch")

    stmt = select(User).where((User.firebase_uid == uid) | (User.email == request.email))
    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        # Create new user
        user = User(
            firebase_uid=uid,
            email=request.email,
            name=request.name,
            role=request.role if request.role in ["admin", "customer"] else "customer",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update existing user if necessary (e.g. link uid)
        if not user.firebase_uid:
            user.firebase_uid = uid
            db.commit()
            db.refresh(user)

    return _issue_tokens(db, user)


def _issue_tokens(db: Session, user: User) -> TokenResponse:
    # Issue tokens
    access_token = create_access_token(subject=user.id)

    # Refresh token: opaque UUID4, hashed for storage
    raw_refresh_token = str(uuid.uuid4())
    hashed_rt = hash_refresh_token(raw_refresh_token)

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db_rt = RefreshToken(
        user_id=user.id,
        token_hash=hashed_rt,
        expires_at=expires_at,
    )
    db.add(db_rt)
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=raw_refresh_token)


def refresh_tokens(db: Session, raw_refresh_token: str) -> TokenResponse:
    h = hash_refresh_token(raw_refresh_token)

    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == h,
        RefreshToken.expires_at > datetime.now(timezone.utc),
    )
    db_rt = db.execute(stmt).scalar_one_or_none()

    if not db_rt:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    user = db.get(User, db_rt.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")

    # Rotate refresh token
    db.delete(db_rt)

    access_token = create_access_token(subject=user.id)
    new_raw_rt = str(uuid.uuid4())
    new_h = hash_refresh_token(new_raw_rt)

    new_db_rt = RefreshToken(
        user_id=user.id,
        token_hash=new_h,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_db_rt)
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=new_raw_rt)


def logout_user(db: Session, user_id: uuid.UUID) -> None:
    stmt = delete(RefreshToken).where(RefreshToken.user_id == user_id)
    db.execute(stmt)
    db.commit()
