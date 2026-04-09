from __future__ import annotations
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import AsyncSessionLocal
from app.db.models.platform import Platform

async def seed_platforms():
    async with AsyncSessionLocal() as db:
        platforms = ["shopee", "lazada", "tiktok", "manual"]
        for p_name in platforms:
            stmt = select(Platform).where(Platform.name == p_name)
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                db.add(Platform(name=p_name))
                print(f"Added platform: {p_name}")
        await db.commit()

if __name__ == "__main__":
    asyncio.run(seed_platforms())
