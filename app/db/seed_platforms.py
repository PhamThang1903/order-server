from __future__ import annotations
from sqlalchemy import select
from app.db.base import SessionLocal
from app.db.models.platform import Platform


def seed_platforms() -> None:
    db = SessionLocal()
    try:
        platforms = ["shopee", "lazada", "tiktok", "manual"]
        for p_name in platforms:
            stmt = select(Platform).where(Platform.name == p_name)
            if not db.execute(stmt).scalar_one_or_none():
                db.add(Platform(name=p_name))
                print(f"Added platform: {p_name}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_platforms()
