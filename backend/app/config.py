"""
Application configuration module.

Loads settings from environment variables using pydantic-settings.
All sensitive values (API keys, secrets) must be provided via environment
variables or a .env file located at the project root.
"""

from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration pulled from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Core ────────────────────────────────────────────────────────────
    APP_NAME: str = "Energy Management SaaS"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ── Security / Auth ─────────────────────────────────────────────────
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPTION_KEY: str  # Fernet-compatible key for field-level encryption

    # ── Database (TimescaleDB / PostgreSQL) ─────────────────────────────
    DATABASE_URL: str  # e.g. postgresql://user:pass@localhost:5432/energy

    # ── Redis / Celery ──────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── CORS ────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _parse_origins(cls, v: str | list[str]) -> list[str]:
        """Accept a comma-separated string *or* an already-parsed list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ── External API keys ───────────────────────────────────────────────
    MOCK_APIS: bool = True  # When True, external calls return fake data

    ENEDIS_API_KEY: str = ""
    ENEDIS_API_BASE_URL: str = "https://ext.hml.api.enedis.fr"

    NEST_CLIENT_ID: str = ""
    NEST_CLIENT_SECRET: str = ""
    NEST_PROJECT_ID: str = ""

    NETATMO_CLIENT_ID: str = ""
    NETATMO_CLIENT_SECRET: str = ""

    OPENWEATHER_API_KEY: str = ""

    # ── Observability ───────────────────────────────────────────────────
    SENTRY_DSN: str = ""

    # ── SMTP / Email ────────────────────────────────────────────────────
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@energy-saas.local"
    SMTP_TLS: bool = True


settings = Settings()  # type: ignore[call-arg]
