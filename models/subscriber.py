from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ── Stripe ──────────────────────────────────────────────────
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # ── CORS ────────────────────────────────────────────────────
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "https://yoursite.com",   # ← update this
    ]

    # ── Database ─────────────────────────────────────────────────
    # Full postgres connection string
    # Format: postgresql://user:password@host:port/dbname
    database_url: str = "postgresql://postgres:password@localhost:5432/mysite"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Single instance imported everywhere
settings = Settings()