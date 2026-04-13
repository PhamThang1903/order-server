from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user import User
from app.core.config import settings

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
