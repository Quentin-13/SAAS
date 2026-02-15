"""
Application configuration module.

Loads settings from environment variables using pydantic-settings.
All sensitive values (API keys, secrets) must be provided via environment
variables or a .env file located at the project root.
"""

from __future__ import annotations

import logging

from cryptography.fernet import Fernet
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_logger = logging.getLogger(__name__)

# Generate a stable default Fernet key for development environments
_DEFAULT_FERNET_KEY = Fernet.generate_key().decode()


class Settings(BaseSettings):
    """Central configuration pulled from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Core ────────────────────────────────────────────────────────────
    APP_NAME: str = "Energy Management SaaS"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ── Security / Auth ─────────────────────────────────────────────────
    SECRET_KEY: str = "dev-secret-key-change-in-production-abc123"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPTION_KEY: str = _DEFAULT_FERNET_KEY  # Fernet-compatible key for field-level encryption

    # ── Database (TimescaleDB / PostgreSQL) ─────────────────────────────
    DATABASE_URL: str = "postgresql://user:password@postgres:5432/energy_autopilot"

    # ── Redis / Celery ──────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── CORS ────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _parse_origins(cls, v: object) -> list[str]:
        """Accept comma-separated string, JSON array, or list."""
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json
                try:
                    return json.loads(v)
                except (json.JSONDecodeError, ValueError):
                    pass
            return [o.strip() for o in v.split(",") if o.strip()]
        if isinstance(v, list):
            return v
        return ["http://localhost:3000"]

    @property
    def allowed_origins_list(self) -> list[str]:
        """Return the parsed CORS origins list."""
        return self.ALLOWED_ORIGINS

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

    # ── Stripe ────────────────────────────────────────────────────────────
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_STARTER: str = ""  # Stripe Price ID for starter plan
    STRIPE_PRICE_PRO: str = ""      # Stripe Price ID for pro plan
    STRIPE_PRICE_ENTERPRISE: str = ""  # Stripe Price ID for enterprise plan
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Rate Limiting ─────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60


settings = Settings()  # type: ignore[call-arg]
