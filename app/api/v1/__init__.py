from __future__ import annotations
from fastapi import APIRouter
from app.api.v1 import auth, users, orders, order_items, platforms, tracking, sync

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(order_items.router, prefix="/orders", tags=["order-items"])
api_router.include_router(platforms.router, prefix="/platforms", tags=["platforms"])
api_router.include_router(tracking.router, prefix="/tracking", tags=["tracking"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
