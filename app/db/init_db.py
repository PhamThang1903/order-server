from __future__ import annotations
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models.user import User
from app.core.config import settings
import urllib.parse


def create_database_if_not_exists() -> None:
    """
    Ensure the target database exists, creating it if necessary.
    Uses psycopg2 directly (sync) to connect to the 'postgres' maintenance DB.
    """
    # Strip the SQLAlchemy driver prefix to get a plain DSN
    raw_url = settings.DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")
    url = urllib.parse.urlparse(raw_url)
    db_name = url.path.lstrip("/")

    # Build a DSN pointing at the 'postgres' maintenance database
    postgres_dsn = raw_url.replace(f"/{db_name}", "/postgres")

    conn = psycopg2.connect(postgres_dsn)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cur.fetchone()
            if not exists:
                cur.execute(f'CREATE DATABASE "{db_name}"')
                print(f"Database '{db_name}' created.")
            else:
                print(f"Database '{db_name}' already exists.")
    finally:
        conn.close()


def init_db(db: Session) -> None:
    """
    Initialize the database with default data (seed admin user).
    """
    admin_email = "qthang193@gmail.com"
    stmt = select(User).where(User.email == admin_email)
    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        user = User(
            email=admin_email,
            name="Super Admin",
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"Default admin user created: {admin_email}")
    else:
        if user.role != "admin":
            user.role = "admin"
            db.commit()
            print(f"User {admin_email} updated to admin role")
        else:
            print(f"Admin user {admin_email} already exists")
