from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from app.core.config import settings
from app.api.v1 import api_router

from app.workers.tracking_worker import scheduler
from app.db.init_db import init_db, create_database_if_not_exists
from app.db.base import SessionLocal, engine, Base
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

limiter = Limiter(key_func=get_remote_address)


def lifespan_startup():
    # Initialize Firebase Admin
    if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        try:
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin initialized successfully")
        except Exception as e:
            logger.error(f"Firebase Admin init failed: {e}")

    # Start Scheduler
    scheduler.start()

    # Ensure target DB exists
    try:
        create_database_if_not_exists()
    except Exception as e:
        logger.error(f"Database creation/check failed: {e}")

    # Create tables
    logger.info("Creating tables if they don't exist...")
    Base.metadata.create_all(bind=engine)

    # Seed default data
    db = SessionLocal()
    try:
        init_db(db)
        logger.info("Database seeding completed")
    finally:
        db.close()


def lifespan_shutdown():
    scheduler.shutdown()


app = FastAPI(title=settings.PROJECT_NAME, on_startup=[lifespan_startup], on_shutdown=[lifespan_shutdown])
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


@app.get("/health")
def health_check():
    db_status = "ok"
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
    except Exception:
        db_status = "error"

    return {
        "status": "ok",
        "database": db_status,
        "scheduler": "running" if scheduler.running else "stopped",
    }


@app.get("/")
def root():
    return {"message": "Order Manager Server API"}
