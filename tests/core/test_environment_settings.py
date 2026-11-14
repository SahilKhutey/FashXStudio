from __future__ import annotations

import pytest
from pydantic import ValidationError

from fashx.core.settings import Settings
from fashx.main import create_app


def valid_staging_kwargs(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "ENV": "staging",
        "APP_ENV": "staging",
        "REPO_BACKEND": "sql",
        "STORAGE_BACKEND": "s3",
        "S3_BUCKET": "fashx-staging-media",
        "S3_USE_IAM_ROLE": True,
        "AUTH_MODE": "jwks",
        "AUTH_JWKS_URL": "https://auth.staging.example.com/.well-known/jwks.json",
        "CORS_ORIGINS": ["https://staging.fashx.com"],
        "DATABASE_URL": "postgresql+asyncpg://staging_user:pass@db.staging.internal:5432/fashx_staging",
        "REDIS_URL": "redis://redis.staging.internal:6379/0",
        "TRYON_PROVIDER": "mock",
    }
    values.update(overrides)
    return values


def valid_prod_kwargs(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "ENV": "prod",
        "APP_ENV": "production",
        "REPO_BACKEND": "sql",
        "STORAGE_BACKEND": "s3",
        "S3_BUCKET": "fashx-prod-media",
        "S3_USE_IAM_ROLE": True,
        "AUTH_MODE": "jwks",
        "AUTH_JWKS_URL": "https://auth.example.com/.well-known/jwks.json",
        "AUTH_ISSUER": "https://auth.example.com",
        "AUTH_AUDIENCE": "fashx-api",
        "CORS_ORIGINS": ["https://app.fashx.com"],
        "DATABASE_URL": "postgresql+asyncpg://prod_user:pass@db.internal:5432/fashx_prod",
        "REDIS_URL": "rediss://redis.internal:6379/0",
        "TRYON_PROVIDER": "fashn_api",
        "FASHN_API_KEY": "live-commercial-test-key",
        "PRIVACY_URL": "https://fashx.com/privacy",
        "TERMS_URL": "https://fashx.com/terms",
        "ENABLE_B2B": False,
    }
    values.update(overrides)
    return values


def test_default_local_configuration_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    settings = Settings()
    assert settings.env == "dev"
    assert settings.app_env == "development"
    assert settings.is_production is False
    assert settings.is_staging is False
    assert settings.is_hosted is False


def test_dev_environment_accepted() -> None:
    settings = Settings(ENV="dev", APP_ENV="development")
    assert settings.env == "dev"
    assert settings.app_env == "development"
    assert settings.is_hosted is False


def test_test_environment_accepted() -> None:
    settings = Settings(ENV="test", APP_ENV="development")
    assert settings.env == "test"
    assert settings.app_env == "development"
    assert settings.is_hosted is False


def test_staging_environment_accepted_with_hosted_safe_settings() -> None:
    settings = Settings(**valid_staging_kwargs())
    assert settings.env == "staging"
    assert settings.app_env == "staging"
    assert settings.is_staging is True
    assert settings.is_hosted is True
    assert settings.is_production is False


def test_prod_environment_accepted_with_production_requirements() -> None:
    settings = Settings(**valid_prod_kwargs())
    assert settings.env == "prod"
    assert settings.app_env == "production"
    assert settings.is_production is True
    assert settings.is_hosted is True
    assert settings.is_staging is False


def test_env_app_env_mismatch_rejected() -> None:
    with pytest.raises(ValidationError, match="Production requires ENV=prod"):
        Settings(ENV="dev", APP_ENV="production")

    with pytest.raises(ValidationError, match="ENV=prod requires APP_ENV=production"):
        Settings(ENV="prod", APP_ENV="development")

    with pytest.raises(ValidationError, match="ENV=staging requires APP_ENV=staging"):
        Settings(ENV="staging", APP_ENV="development")

    with pytest.raises(ValidationError, match="ENV=dev requires APP_ENV=development"):
        Settings(ENV="dev", APP_ENV="staging")


def test_staging_refuses_memory_repo() -> None:
    with pytest.raises(ValidationError, match="staging requires REPO_BACKEND=sql"):
        Settings(**valid_staging_kwargs(REPO_BACKEND="memory"))


def test_staging_refuses_local_storage() -> None:
    with pytest.raises(ValidationError, match="staging requires STORAGE_BACKEND=s3"):
        Settings(**valid_staging_kwargs(STORAGE_BACKEND="local"))


def test_staging_refuses_local_auth() -> None:
    with pytest.raises(ValidationError, match="staging requires AUTH_MODE=jwks"):
        Settings(**valid_staging_kwargs(AUTH_MODE="local"))


def test_staging_refuses_wildcard_cors() -> None:
    with pytest.raises(ValidationError, match="wildcard CORS not allowed in staging"):
        Settings(**valid_staging_kwargs(CORS_ORIGINS=["*"]))


def test_staging_refuses_missing_s3_bucket() -> None:
    with pytest.raises(ValidationError, match="staging requires S3_BUCKET"):
        Settings(**valid_staging_kwargs(S3_BUCKET=None))


def test_prod_refuses_mock_tryon() -> None:
    with pytest.raises(ValidationError, match="prod requires non-mock TRYON_PROVIDER"):
        Settings(**valid_prod_kwargs(TRYON_PROVIDER="mock"))


def test_prod_refuses_selfhost_placeholder_tryon() -> None:
    with pytest.raises(ValidationError, match="fashn_selfhost is not implemented"):
        Settings(**valid_prod_kwargs(TRYON_PROVIDER="fashn_selfhost"))


def test_prod_refuses_local_jwt_auth() -> None:
    with pytest.raises(ValidationError, match="prod requires AUTH_MODE=jwks"):
        Settings(**valid_prod_kwargs(AUTH_MODE="local"))


def test_prod_refuses_wildcard_cors() -> None:
    with pytest.raises(ValidationError, match="wildcard CORS not allowed in prod"):
        Settings(**valid_prod_kwargs(CORS_ORIGINS=["*"]))


def test_prod_refuses_http_cors() -> None:
    with pytest.raises(ValidationError, match="Production CORS origins must use HTTPS"):
        Settings(**valid_prod_kwargs(CORS_ORIGINS=["http://insecure.example.com"]))


def test_prod_refuses_missing_privacy_or_terms() -> None:
    with pytest.raises(ValidationError, match="prod requires PRIVACY_URL and TERMS_URL"):
        Settings(**valid_prod_kwargs(PRIVACY_URL=None))

    with pytest.raises(ValidationError, match="prod requires PRIVACY_URL and TERMS_URL"):
        Settings(**valid_prod_kwargs(TERMS_URL=None))


def test_prod_refuses_missing_storage_credentials_when_not_iam() -> None:
    with pytest.raises(ValidationError, match="S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY"):
        Settings(**valid_prod_kwargs(S3_USE_IAM_ROLE=False, S3_ACCESS_KEY_ID=None))


def test_prod_refuses_b2b_enabled() -> None:
    with pytest.raises(ValidationError, match="ENABLE_B2B must be false in prod for MVP"):
        Settings(**valid_prod_kwargs(ENABLE_B2B=True))


def test_create_app_invokes_release_validation_in_hosted_mode() -> None:
    # Staging app creation succeeds with valid staging settings
    staging_settings = Settings(**valid_staging_kwargs())
    app = create_app(staging_settings)
    assert app is not None

    # Staging app creation fails if release config invariant is broken (e.g. invalid CORS origin)
    invalid_staging_settings = Settings(**valid_staging_kwargs(CORS_ORIGINS=["ftp://invalid-origin.com"]))
    with pytest.raises(ValueError, match="Invalid CORS origin format"):
        create_app(invalid_staging_settings)
