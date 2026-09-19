"""
Base Settings using pydantic-settings v2
Fails fast on startup if configuration invariants are violated.
"""

from enum import Enum
from functools import lru_cache
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class ModelStatus(str, Enum):
    RESEARCH = "research"
    EVALUATION = "evaluation"
    COMMERCIAL_APPROVED = "commercial-approved"
    DISABLED = "disabled"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Environment
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT
    DEBUG: bool = True
    PORT: int = 8000
    SECRET_KEY: str = Field(
        default="local-dev-insecure-secret-key-must-be-changed-in-prod-at-least-32-chars",
        min_length=32,
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://fashx_user:fashx_password@localhost:5432/fashx_db"
    )
    DATABASE_URL_SYNC: str = Field(
        default="postgresql://fashx_user:fashx_password@localhost:5432/fashx_db"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # Storage
    STORAGE_BACKEND: str = Field(default="local")  # local | s3 | r2
    STORAGE_LOCAL_DIR: str = Field(default="./storage")
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET_NAME: str = "fashx-media"
    S3_REGION: str = "ap-south-1"

    # Virtual Try-On Model Licensing & Configuration
    ACTIVE_TRYON_MODEL: str = "idm_vton_v1"
    ACTIVE_TRYON_MODEL_STATUS: ModelStatus = ModelStatus.EVALUATION
    ACTIVE_TRYON_MODEL_WEIGHTS: str = "weights_2026_08"
    TRYON_PREPROCESSING_VERSION: str = "sam_bisenet_v2"

    # Security & Capabilities
    CAPABILITY_TOKEN_SECRET: str = Field(
        default="local-capability-token-secret-must-be-changed-in-production",
        min_length=16,
    )
    CAPABILITY_TOKEN_TTL_SECONDS: int = 900

    @field_validator("ACTIVE_TRYON_MODEL_STATUS")
    @classmethod
    def validate_production_model_license(cls, v: ModelStatus, info) -> ModelStatus:
        env = info.data.get("ENVIRONMENT", EnvironmentType.DEVELOPMENT)
        if env == EnvironmentType.PRODUCTION and v != ModelStatus.COMMERCIAL_APPROVED:
            raise ValueError(
                f"Production deployment blocked: Active model status is '{v}'. "
                "Only 'commercial-approved' models may be deployed to production (Rule I19)."
            )
        return v


@lru_cache()
def get_settings() -> Settings:
    return Settings()
