from __future__ import annotations
import logging
from sqlalchemy import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.db.base import AsyncSessionLocal
from app.db.models.order import Order
from app.services import tracking_service

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job("interval", hours=1, id="order_tracking")
async def run_tracking_job():
    """
    Query orders eligible for tracking:
    - status NOT IN ('delivered', 'cancelled', 'returned')
    - tracking_url IS NOT NULL
    - tracking_retry_count < 3
    - is_deleted = FALSE
    """
    logger.info("Starting order tracking job...")
    async with AsyncSessionLocal() as db:
        stmt = select(Order).where(
            Order.status.not_in(["delivered", "cancelled", "returned"]),
            Order.tracking_url.isnot(None),
            Order.tracking_retry_count < 3,
            Order.is_deleted == False
        )
        result = await db.execute(stmt)
        orders = result.scalars().all()
        
        logger.info(f"Found {len(orders)} orders to track.")
        for order in orders:
            try:
                changed = await tracking_service.fetch_and_update(db, order)
                if changed:
                    logger.info(f"Order {order.order_code} updated via tracking.")
            except Exception as e:
                logger.error(f"Tracking failed for order {order.order_code}: {e}")
    logger.info("Order tracking job completed.")
