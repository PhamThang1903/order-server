from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from app.core.dependencies import get_db, get_current_user
from app.db.models.platform import Platform

router = APIRouter()


class PlatformResponse(BaseModel):
    id: UUID
    name: str
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[PlatformResponse])
def list_platforms(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.execute(select(Platform)).scalars().all()
