from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Order Manager Server"
    API_V1_STR: str = "/api/v1"

    # DATABASE — sync psycopg2 driver
    DATABASE_URL: str = Field(default="postgresql+psycopg2://postgres:postgres@localhost/ordermanager")

    # AUTH
    SECRET_KEY: str = Field(default="secret-key-change-me")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # FIREBASE
    FIREBASE_SERVICE_ACCOUNT_JSON: str | None = None

    # S3 / R2
    S3_BUCKET_NAME: str | None = None
    S3_PUBLIC_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

settings = Settings()
