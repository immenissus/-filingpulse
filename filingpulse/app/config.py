"""
app/config.py
=============
Application configuration loaded from environment variables via Pydantic
BaseSettings.  All secrets (DB URL, SMTP password, etc.) live in .env and
are never hard-coded.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # App
    # ------------------------------------------------------------------
    app_name: str = "FilingPulse"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    secret_key: str = Field(..., min_length=32)
    cors_origins: list[str] = Field(
        default=["*"],
        description="Comma-separated allowed origins for CORS. Automatically parsed into a list."
    )

    # ------------------------------------------------------------------
    # Admin
    # ------------------------------------------------------------------
    admin_api_key: str = Field(
        ...,
        description="Bearer token required for admin-only endpoints (POST /jurisdictions).",
    )

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    database_url: PostgresDsn = Field(
        ...,
        description=(
            "Async PostgreSQL DSN.  Must use the asyncpg driver: "
            "postgresql+asyncpg://user:pass@host/dbname"
        ),
    )

    # SQLAlchemy async pool settings
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30

    # ------------------------------------------------------------------
    # Geocoder (US Census Bureau — no key required)
    # ------------------------------------------------------------------
    census_geocoder_url: str = (
        "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    )
    census_geocoder_benchmark: str = "Public_AR_Current"
    census_geocoder_timeout: int = 10  # seconds
    census_geocoder_retries: int = 3

    # ------------------------------------------------------------------
    # Email — SMTP (default) or Resend
    # ------------------------------------------------------------------
    email_backend: Literal["smtp", "resend"] = "smtp"

    # SMTP settings (used when email_backend == "smtp")
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    smtp_from_address: str = "noreply@filingpulse.local"
    smtp_from_name: str = "FilingPulse Alerts"

    # Resend settings (used when email_backend == "resend")
    resend_api_key: str | None = None
    resend_from_address: str = "noreply@filingpulse.local"
    resend_api_url: str = "https://api.resend.com/emails"

    # ------------------------------------------------------------------
    # Rate limiting (slowapi / Redis-backed in production)
    # ------------------------------------------------------------------
    # GET /filings is rate-limited; adjust for your traffic
    filings_rate_limit: str = "60/minute"

    # ------------------------------------------------------------------
    # Scheduler
    # ------------------------------------------------------------------
    scheduler_timezone: str = "UTC"
    # Default poll interval if not overridden per-jurisdiction (seconds)
    default_poll_interval_seconds: int = 86_400

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("database_url", mode="before")
    @classmethod
    def _require_asyncpg(cls, v: str) -> str:
        if "asyncpg" not in str(v):
            raise ValueError(
                "DATABASE_URL must use the asyncpg driver: "
                "postgresql+asyncpg://..."
            )
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_origins(cls, v: any) -> list[str]:
        if isinstance(v, str):
            return [o.strip() for p in v.split(",") for o in [p.strip()] if o]
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached singleton Settings instance."""
    return Settings()  # type: ignore[call-arg]
