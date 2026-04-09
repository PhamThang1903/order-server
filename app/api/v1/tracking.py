from __future__ import annotations
import httpx
import time
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict
from app.core.dependencies import get_db, require_admin
from app.db.models.order import Order
from app.db.models.tracking_provider import TrackingProvider
from app.services import tracking_service

router = APIRouter()

class ProviderResponse(BaseModel):
    id: UUID
    provider: str
    base_url: str
    auth_header_key: str | None
    auth_header_value: str | None
    is_enabled: bool
    model_config = ConfigDict(from_attributes=True)

class ProviderUpdate(BaseModel):
    base_url: str | None = None
    auth_header_key: str | None = None
    auth_header_value: str | None = None
    is_enabled: bool | None = None

@router.get("/providers", response_model=list[ProviderResponse])
async def list_providers(
    current_admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(TrackingProvider))
    return result.scalars().all()

@router.patch("/providers/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: UUID,
    provider_in: ProviderUpdate,
    current_admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    provider = await db.get(TrackingProvider, provider_id)
    if not provider:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    
    update_data = provider_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(provider, field, value)
        
    await db.commit()
    await db.refresh(provider)
    return provider

@router.post("/providers/{provider_id}/test")
async def test_provider_connection(
    provider_id: UUID,
    current_admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    provider = await db.get(TrackingProvider, provider_id)
    if not provider:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
         
    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(provider.base_url)
            # Just test if we get ANY response from the base URL
            latency = (time.time() - start_time) * 1000
            return {"success": resp.status_code < 500, "latency_ms": round(latency, 2)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/orders/{order_id}/track")
async def manual_trigger_tracking(
    order_id: UUID,
    current_admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    order = await db.get(Order, order_id)
    if not order or order.is_deleted:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
         
    changed = await tracking_service.fetch_and_update(db, order)
    return {"success": True, "changed": changed}
