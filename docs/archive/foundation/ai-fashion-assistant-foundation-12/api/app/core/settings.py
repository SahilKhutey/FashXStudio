from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = Field(default="development", validation_alias="APP_ENV")
    app_name: str = Field(default="AI Fashion Assistant API", validation_alias="APP_NAME")
    app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    cors_origins: list[str] = Field(default=["http://localhost:8081"], validation_alias="CORS_ORIGINS")
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
    internal_service_token: str | None = Field(default=None, validation_alias="INTERNAL_SERVICE_TOKEN")
    r2_endpoint_url: str | None = Field(default=None, validation_alias="R2_ENDPOINT_URL")
    r2_access_key_id: str | None = Field(default=None, validation_alias="R2_ACCESS_KEY_ID")
    r2_secret_access_key: str | None = Field(default=None, validation_alias="R2_SECRET_ACCESS_KEY")
    r2_bucket: str | None = Field(default=None, validation_alias="R2_BUCKET")
    r2_region: str = Field(default="auto", validation_alias="R2_REGION")
    r2_upload_url_ttl_seconds: int = Field(default=900, ge=60, le=3600, validation_alias="R2_UPLOAD_URL_TTL_SECONDS")
    r2_download_url_ttl_seconds: int = Field(default=900, ge=60, le=3600, validation_alias="R2_DOWNLOAD_URL_TTL_SECONDS")
    api_base_url: str = Field(default="http://127.0.0.1:8000", validation_alias="API_BASE_URL")
    worker_http_timeout_seconds: float = Field(default=15.0, ge=1.0, le=60.0, validation_alias="WORKER_HTTP_TIMEOUT_SECONDS")
    profile_photo_max_attempts: int = Field(default=3, ge=1, le=10, validation_alias="PROFILE_PHOTO_MAX_ATTEMPTS")
    profile_photo_max_bytes: int = Field(default=15 * 1024 * 1024, ge=1024, le=50 * 1024 * 1024, validation_alias="PROFILE_PHOTO_MAX_BYTES")
    profile_photo_lock_timeout_seconds: int = Field(default=300, ge=30, le=3600, validation_alias="PROFILE_PHOTO_LOCK_TIMEOUT_SECONDS")
    pose_provider: str = Field(default="opencv_heuristic", validation_alias="POSE_PROVIDER")
    pose_model_path: str | None = Field(default=None, validation_alias="POSE_MODEL_PATH")
    capture_quality_threshold: float = Field(default=0.55, ge=0.0, le=1.0, validation_alias="CAPTURE_QUALITY_THRESHOLD")
    affiliate_network: str = Field(default="mvp", min_length=1, max_length=64, validation_alias="AFFILIATE_NETWORK")
    affiliate_tracking_param: str = Field(default="afa_click_id", min_length=1, max_length=64, validation_alias="AFFILIATE_TRACKING_PARAM")
    affiliate_source_param: str = Field(default="afa_source", max_length=64, validation_alias="AFFILIATE_SOURCE_PARAM")

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
