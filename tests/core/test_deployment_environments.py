"""Tests for FashXStudio multi-environment deployment configurations.

Validates that environment invariants, IAM task role configurations,
TLS certificate requirements, and release gates are enforced across
development, staging, and production.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from fashx.core.release_config import validate_release_config
from fashx.core.settings import Settings


def staging_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "env": "staging",
        "app_env": "staging",
        "repo_backend": "sql",
        "storage_backend": "s3",
        "s3_bucket": "fashx-staging-private-test",
        "s3_use_iam_role": True,
        "auth_mode": "jwks",
        "auth_issuer": "https://auth-staging.example.com",
        "auth_audience": "fashx-api",
        "auth_jwks_url": "https://auth-staging.example.com/.well-known/jwks.json",
        "database_url": "postgresql+asyncpg://test:test@localhost:5432/fashx_staging",
        "redis_url": "rediss://localhost:6379/0",
        "readiness_requires_database": True,
        "db_ssl_ca_file": "/tmp/test-rds-ca.pem",
        "cors_origins": ["https://staging.example.com"],
        "tryon_provider": "mock",
        "enable_b2b": False,
        "privacy_url": "https://example.com/privacy",
        "terms_url": "https://example.com/terms",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def prod_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "env": "prod",
        "app_env": "production",
        "repo_backend": "sql",
        "storage_backend": "s3",
        "s3_bucket": "fashx-prod-private-test",
        "s3_use_iam_role": True,
        "auth_mode": "jwks",
        "auth_issuer": "https://auth.example.com",
        "auth_audience": "fashx-api",
        "auth_jwks_url": "https://auth.example.com/.well-known/jwks.json",
        "database_url": "postgresql+asyncpg://prod_user:pass@db.internal:5432/fashx_prod",
        "redis_url": "rediss://:auth_token@redis.internal:6379/0",
        "readiness_requires_database": True,
        "db_ssl_ca_file": "/etc/ssl/certs/aws-rds-global-bundle.pem",
        "cors_origins": ["https://app.fashx.com"],
        "tryon_provider": "fashn_api",
        "fashn_api_key": "live-test-key",
        "enable_b2b": False,
        "privacy_url": "https://fashx.com/privacy",
        "terms_url": "https://fashx.com/terms",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_staging_configuration_is_valid() -> None:
    settings = staging_settings()
    assert settings.env == "staging"
    assert settings.app_env == "staging"
    assert settings.is_staging is True
    assert settings.is_hosted is True
    assert settings.db_ssl_ca_file == "/tmp/test-rds-ca.pem"
    assert settings.db_pool_timeout_s == 20


def test_staging_release_config_validation_passes() -> None:
    settings = staging_settings()
    validate_release_config(settings.to_release_config())


def test_staging_rejects_missing_s3_bucket() -> None:
    with pytest.raises(ValidationError, match="staging requires S3_BUCKET"):
        staging_settings(s3_bucket=None)


def test_staging_rejects_static_credentials_when_using_iam_role() -> None:
    with pytest.raises(
        ValidationError,
        match="Do not configure static S3 credentials when using ECS task roles",
    ):
        staging_settings(
            s3_use_iam_role=True,
            s3_access_key_id="AKIAEXAMPLESTATICKEY",
        )


def test_production_configuration_is_valid() -> None:
    settings = prod_settings()
    assert settings.env == "prod"
    assert settings.app_env == "production"
    assert settings.is_production is True
    assert settings.is_hosted is True
    assert settings.db_ssl_ca_file == "/etc/ssl/certs/aws-rds-global-bundle.pem"


def test_production_rejects_static_credentials_when_using_iam_role() -> None:
    with pytest.raises(
        ValidationError,
        match="Do not configure static S3 credentials when using ECS task roles",
    ):
        prod_settings(
            s3_use_iam_role=True,
            s3_access_key_id="AKIAEXAMPLESTATICKEY",
        )


def test_production_release_config_rejects_unencrypted_redis() -> None:
    settings = prod_settings(redis_url="redis://insecure.internal:6379/0")
    with pytest.raises(ValueError, match="requires TLS-encrypted Redis connection"):
        validate_release_config(settings.to_release_config())


def test_shared_development_configuration_is_valid() -> None:
    settings = Settings(
        _env_file=None,
        env="dev",
        app_env="development",
        repo_backend="sql",
        storage_backend="s3",
        s3_bucket="fashx-dev-private-test",
        s3_use_iam_role=True,
        auth_mode="jwks",
        auth_jwks_url="https://auth-dev.example.com/.well-known/jwks.json",
        tryon_provider="mock",
    )
    assert settings.env == "dev"
    assert settings.app_env == "development"
    assert settings.is_hosted is False


def test_env_and_app_env_consistency_enforced() -> None:
    with pytest.raises(ValidationError, match="requires APP_ENV="):
        Settings(_env_file=None, env="staging", app_env="development")

    with pytest.raises(ValidationError, match="requires APP_ENV="):
        Settings(_env_file=None, env="prod", app_env="staging")
