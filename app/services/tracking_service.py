from __future__ import annotations
import httpx
import logging
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.order import Order
from app.db.models.status_history import StatusHistory
from app.db.models.tracking_provider import TrackingProvider
from app.services import fcm_service
from app.parsers import ghn_parser, ghtk_parser, jnt_parser
from app.schemas.tracking import TrackingResult

logger = logging.getLogger(__name__)

async def get_provider_config(db: AsyncSession, provider_name: str) -> TrackingProvider | None:
    stmt = select(TrackingProvider).where(TrackingProvider.provider == provider_name)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def fetch_and_update(db: AsyncSession, order: Order) -> bool:
    """Returns True if any change was detected and saved."""
    if not order.tracking_provider or not order.tracking_url:
        return False
        
    provider = await get_provider_config(db, order.tracking_provider)
    if not provider or not provider.is_enabled:
         return False

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            headers = {}
            if provider.auth_header_key and provider.auth_header_value:
                headers[provider.auth_header_key] = provider.auth_header_value
            
            resp = await client.get(order.tracking_url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, httpx.TimeoutException) as e:
        logger.error(f"Tracking HTTP error for order {order.order_code}: {e}")
        await increment_retry(db, order)
        if order.tracking_retry_count >= 3:
            await fcm_service.notify_tracking_error(db, order)
        return False
    except Exception as e:
        logger.error(f"Tracking unknown error for order {order.order_code}: {e}")
        return False

    result = parse_response(order.tracking_provider, data, order.id)
    
    # Check for actual changes
    is_status_changed = result.new_status and result.new_status != order.status
    is_location_changed = result.new_location and result.new_location != order.current_location
    
    if not (is_status_changed or is_location_changed):
        await reset_retry(db, order)
        return False

    # Apply changes
    old_status = order.status
    old_location = order.current_location
    
    if result.new_status:
        order.status = result.new_status
    if result.new_location:
         order.current_location = result.new_location
    if result.shipper_phone:
         order.shipper_phone = result.shipper_phone
         
    order.last_tracked_at = datetime.now(timezone.utc)
    order.updated_at = datetime.now(timezone.utc)
    
    # Write history
    history = StatusHistory(
        order_id=order.id,
        old_status=old_status,
        new_status=order.status,
        old_location=old_location,
        new_location=order.current_location,
        changed_by="system",
        source="auto_tracking"
    )
    db.add(history)
    
    # Send FCM
    await fcm_service.notify_status_or_location_changed(
        db, order, 
        result.new_status if is_status_changed else None,
        result.new_location if is_location_changed else None
    )
    
    await reset_retry(db, order)
    await db.commit()
    return True

def parse_response(provider_name: str, data: dict, order_id: UUID) -> TrackingResult:
    parsers = {"ghn": ghn_parser, "ghtk": ghtk_parser, "jnt": jnt_parser}
    if provider_name not in parsers:
        raise ValueError(f"Unknown provider: {provider_name}")
    return parsers[provider_name].parse(data, order_id)

async def increment_retry(db: AsyncSession, order: Order):
    order.tracking_retry_count += 1
    order.last_tracked_at = datetime.now(timezone.utc)
    await db.commit()

async def reset_retry(db: AsyncSession, order: Order):
    order.tracking_retry_count = 0
    await db.commit()
