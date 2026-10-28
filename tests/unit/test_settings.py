import pytest
from pydantic import ValidationError

from fashx.core.settings import Settings


def test_production_settings_flag() -> None:
    settings = Settings(
        ENV="prod",
        APP_ENV="production",
        REPO_BACKEND="sql",
        STORAGE_BACKEND="s3",
        S3_BUCKET="test-bucket",
        S3_USE_IAM_ROLE=True,
        AUTH_MODE="jwks",
        AUTH_JWKS_URL="https://auth.example.com/.well-known/jwks.json",
        TRYON_PROVIDER="fashn_api",
        FASHN_API_KEY="test-key",
        PRIVACY_URL="https://example.com/privacy",
        TERMS_URL="https://example.com/terms",
        CORS_ORIGINS=["https://app.example.com"],
    )
    assert settings.is_production is True


def test_production_requires_env_prod() -> None:
    with pytest.raises(ValidationError, match="Production requires ENV=prod"):
        Settings(APP_ENV="production", ENV="dev")


def test_development_defaults() -> None:
    settings = Settings(APP_ENV="development")
    assert settings.readiness_requires_database is False
