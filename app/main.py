from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials

from app.core.config import settings
from app.api.v1 import api_router

from app.workers.tracking_worker import scheduler
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Firebase Admin
    if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        try:
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Firebase Admin init failed: {e}")
            
    # Start Scheduler
    scheduler.start()
    yield
    # Shutdown Scheduler
    scheduler.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

from app.db.base import AsyncSessionLocal
from sqlalchemy import text

@app.get("/health")
async def health_check():
    # 1. DB check
    db_status = "ok"
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
        
    return {
        "status": "ok",
        "database": db_status,
        "scheduler": "running" if scheduler.running else "stopped"
    }

@app.get("/")
async def root():
    return {"message": "Order Manager Server API"}
