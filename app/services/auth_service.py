from __future__ import annotations
from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException, status
from firebase_admin import auth
from app.core.config import settings
from app.core.security import create_access_token, hash_refresh_token
from app.db.models.user import User
from app.db.models.refresh_token import RefreshToken
from app.schemas.auth import TokenResponse

async def login_with_firebase(db: AsyncSession, firebase_id_token: str) -> TokenResponse:
    try:
        decoded_token = auth.verify_id_token(firebase_id_token)
        uid = decoded_token.get("uid")
        email = decoded_token.get("email")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase ID token")

    stmt = select(User).where((User.firebase_uid == uid) | (User.email == email))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not registered. Contact admin.")
    
    # Link firebase_uid if missing
    if not user.firebase_uid:
        user.firebase_uid = uid
        await db.commit()
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    # Issue tokens
    access_token = create_access_token(subject=user.id)
    
    # Refresh token: opaque UUID4, then hashed for storage
    raw_refresh_token = str(uuid.uuid4())
    hashed_rt = hash_refresh_token(raw_refresh_token)
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    db_rt = RefreshToken(
        user_id=user.id,
        token_hash=hashed_rt,
        expires_at=expires_at
    )
    db.add(db_rt)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token
    )

async def refresh_tokens(db: AsyncSession, raw_refresh_token: str) -> TokenResponse:
    # Note: In practice, storing raw opaque tokens and hashing them is more secure.
    # To find the user or token, we'd need to search or store a token ID in the access token.
    # However, 'refresh_token rotation' with opaque tokens usually means we lookup by the token itself.
    # But if we hash them, we can't search easily.
    # A common way: opaque token has some identifier or we use a RefreshToken ID in the payload.
    # But spec says: "lookup in refresh_tokens". 
    # For simplicity, if we hash it, we'd have to find it.
    # If the database is large, hashing without an ID is slow.
    # I'll store the token itself for now or use a simpler hash if searching by token.
    # Wait, spec says: "Hash incoming token, lookup in refresh_tokens".
    
    from app.core.security import hash_refresh_token
    h = hash_refresh_token(raw_refresh_token)
    
    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == h,
        RefreshToken.expires_at > datetime.now(timezone.utc)
    )
    result = await db.execute(stmt)
    db_rt = result.scalar_one_or_none()
    
    if not db_rt:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    
    user = await db.get(User, db_rt.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")
        
    # Rotate refresh token
    await db.delete(db_rt)
    
    access_token = create_access_token(subject=user.id)
    new_raw_rt = str(uuid.uuid4())
    new_h = hash_refresh_token(new_raw_rt)
    
    new_db_rt = RefreshToken(
        user_id=user.id,
        token_hash=new_h,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(new_db_rt)
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_raw_rt
    )

async def logout_user(db: AsyncSession, user_id: uuid.UUID):
    stmt = delete(RefreshToken).where(RefreshToken.user_id == user_id)
    await db.execute(stmt)
    await db.commit()
