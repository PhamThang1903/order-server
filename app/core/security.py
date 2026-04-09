from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
import firebase_admin
from firebase_admin import auth, credentials
from app.core.config import settings

# Password context for refresh token hash (though we use opaque UUID hashed)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_firebase_id_token(id_token: str) -> dict | None:
    try:
        # Verify the ID token and return claims
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception:
        return None

def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

import hashlib

def hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode()).hexdigest()
