from __future__ import annotations
import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user import User
from app.core.config import settings
from typing import Optional
import urllib.parse

async def create_database_if_not_exists() -> None:
    """
    Ensure the target database exists, creating it if necessary.
    """
    # Parse the DATABASE_URL. It might have 'postgresql+asyncpg://'
    parsed_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgres://")
    url = urllib.parse.urlparse(parsed_url)
    db_name = url.path[1:]
    
    # Connection string to 'postgres' database to check/create the target database
    # We replace the database name in the DSN with 'postgres'
    postgres_dsn = parsed_url.replace(f"/{db_name}", "/postgres")
    
    conn = await asyncpg.connect(postgres_dsn)
    try:
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if not exists:
            # We must close the connection and reopen or just use the current one if it's 'postgres'
            # Note: CREATE DATABASE cannot be run in a transaction block
            # asyncpg by default doesn't start a transaction for simple commands like this
            await conn.execute(f"CREATE DATABASE {db_name}")
            print(f"Database '{db_name}' created.")
        else:
            print(f"Database '{db_name}' already exists.")
    finally:
        await conn.close()

async def init_db(db: AsyncSession) -> None:
    """
    Initialize the database with default data.
    """
    # 1. Seed Admin User
    admin_email = "qthang193@gmail.com"
    stmt = select(User).where(User.email == admin_email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            email=admin_email,
            name="Super Admin",
            role="admin",
            is_active=True
        )
        db.add(user)
        await db.commit()
        print(f"Default admin user created: {admin_email}")
    else:
        # Ensure it's an admin if it exists
        if user.role != "admin":
            user.role = "admin"
            await db.commit()
            print(f"User {admin_email} updated to admin role")
        else:
            print(f"Admin user {admin_email} already exists")
