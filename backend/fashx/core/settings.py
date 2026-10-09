from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    env: Literal["dev", "test", "prod"] = Field(default="dev", validation_alias="ENV")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    app_name: str = Field(default="AI Fashion Assistant API", validation_alias="APP_NAME")
    app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    cors_origins: list[str] = Field(
        default=["http://localhost:8081"], validation_alias="CORS_ORIGINS"
    )
    database_url: str = Field(
        default="postgresql+asyncpg://fashion:fashion@localhost:5432/fashion",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    readiness_requires_database: bool = Field(
        default=False,
        validation_alias="READINESS_REQUIRES_DATABASE",
    )
    sentry_dsn: str | None = Field(default=None, validation_alias="SENTRY_DSN")
    sentry_environment: str = Field(default="development", validation_alias="SENTRY_ENVIRONMENT")
    enable_frozen: bool = Field(
        default=False,
        validation_alias="FASHX_ENABLE_FROZEN",
    )
    feature_flags: dict[str, bool] = Field(
        default_factory=dict,
        validation_alias="FEATURE_FLAGS",
        description="JSON object of feature-id to enabled-state runtime overrides.",
    )

    auth_mode: Literal["local", "jwks"] = Field(default="local", validation_alias="AUTH_MODE")
    auth_issuer: str = Field(default="fashx-local", validation_alias="AUTH_ISSUER")
    auth_audience: str = Field(default="fashx-api", validation_alias="AUTH_AUDIENCE")
    auth_jwt_secret: SecretStr | None = Field(default=None, validation_alias="AUTH_JWT_SECRET")
    auth_jwks_url: str | None = Field(default=None, validation_alias="AUTH_JWKS_URL")
    internal_service_token: str | None = Field(default=None, validation_alias="INTERNAL_SERVICE_TOKEN")

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in ("production", "prod") or self.env == "prod"

    @model_validator(mode="after")
    def _fail_fast(self) -> "Settings":
        if self.auth_mode == "local" and not self.auth_jwt_secret:
            raise ValueError("AUTH_JWT_SECRET required in local auth mode")
        if self.env == "prod":
            if self.auth_mode != "jwks" or not self.auth_jwks_url:
                raise ValueError("prod requires AUTH_MODE=jwks and AUTH_JWKS_URL")
            if "*" in self.cors_origins:
                raise ValueError("wildcard CORS not allowed in prod")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

