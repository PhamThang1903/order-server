from __future__ import annotations
from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str = ""
    is_active: bool = True

class UserCreate(UserBase):
    firebase_uid: str | None = None
    role: str = "customer" # 'admin' | 'customer'

class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    fcm_token: str | None = None

class UserResponse(UserBase):
    id: UUID
    role: str
    firebase_uid: str | None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
