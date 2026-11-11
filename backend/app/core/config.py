from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. Required values fail fast at startup. Secrets are never logged."""

    # Repo-root .env (backend runs from backend/). Real environment variables take precedence.
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), extra="ignore", case_sensitive=False
    )

    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"

    supabase_url: str = Field(..., min_length=1)
    supabase_jwt_audience: str = "authenticated"
    supabase_jwt_secret: str | None = Field(default=None, repr=False)

    database_url: str = Field(..., min_length=1, repr=False)
    migration_database_url: str | None = Field(default=None, repr=False)

    # AI provider (optional; deterministic fallback when unset)
    gemini_api_key: str | None = Field(default=None, repr=False)
    gemini_model: str = "gemini-2.5-flash"

    # Resume upload and parsing (contract §5, §16)
    resume_max_bytes: int = 5_242_880  # 5 MiB
    resume_parse_max_concurrency: int = 2
    rate_limit_resume_parses_per_hour: int = 10

    # Task runner (contract §2, §16)
    task_timeout_resume_parse_seconds: int = 60
    task_watchdog_interval_seconds: int = 60
    task_watchdog_grace_seconds: int = 30

    @field_validator("supabase_url")
    @classmethod
    def _strip_url(cls, v: str) -> str:
        return v.rstrip("/")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def jwt_issuer(self) -> str:
        return f"{self.supabase_url}/auth/v1"

    @property
    def jwks_url(self) -> str:
        return f"{self.supabase_url}/auth/v1/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
