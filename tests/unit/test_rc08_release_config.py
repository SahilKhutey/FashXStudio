from __future__ import annotations

import pytest

from fashx.core.release_config import ReleaseConfig, validate_release_config


def production_config(**overrides: object) -> ReleaseConfig:
    values: dict[str, object] = {
        "app_env": "production",
        "auth_mode": "jwks",
        "database_url": "postgresql://user:pass@db.internal:5432/fashx_prod",
        "redis_url": "rediss://redis.internal:6379/0",
        "storage_backend": "s3",
        "tryon_provider": "fashn_api",
        "cors_origins": ["https://app.fashx.com"],
        "debug": False,
    }
    values.update(overrides)
    return ReleaseConfig(**values)  # type: ignore[arg-type]


def staging_config(**overrides: object) -> ReleaseConfig:
    values: dict[str, object] = {
        "app_env": "staging",
        "auth_mode": "jwks",
        "database_url": "postgresql://user:pass@db.staging.internal:5432/fashx_staging",
        "redis_url": "redis://redis.staging.internal:6379/0",
        "storage_backend": "s3",
        "tryon_provider": "mock",
        "cors_origins": ["https://staging.fashx.com"],
        "debug": False,
    }
    values.update(overrides)
    return ReleaseConfig(**values)  # type: ignore[arg-type]


def test_valid_production_configuration() -> None:
    validate_release_config(production_config())


def test_production_rejects_local_auth() -> None:
    with pytest.raises(ValueError, match="requires JWKS authentication"):
        validate_release_config(production_config(auth_mode="local"))


def test_production_rejects_debug() -> None:
    with pytest.raises(ValueError, match="Debug mode is strictly forbidden"):
        validate_release_config(production_config(debug=True))


def test_production_rejects_local_storage() -> None:
    with pytest.raises(ValueError, match="requires private object storage"):
        validate_release_config(production_config(storage_backend="local"))


def test_production_rejects_mock_tryon() -> None:
    with pytest.raises(ValueError, match="mock forbidden"):
        validate_release_config(production_config(tryon_provider="mock"))


def test_production_rejects_empty_or_wildcard_cors() -> None:
    with pytest.raises(ValueError, match="CORS origins cannot be empty"):
        validate_release_config(production_config(cors_origins=[]))

    with pytest.raises(ValueError, match="Wildcard CORS origin is forbidden"):
        validate_release_config(production_config(cors_origins=["*"]))


def test_production_requires_https_cors() -> None:
    with pytest.raises(ValueError, match="must use HTTPS"):
        validate_release_config(production_config(cors_origins=["http://insecure.example.com"]))


def test_valid_staging_configuration() -> None:
    validate_release_config(staging_config())


def test_staging_rejects_local_auth() -> None:
    with pytest.raises(ValueError, match="requires JWKS authentication"):
        validate_release_config(staging_config(auth_mode="local"))


def test_staging_rejects_debug() -> None:
    with pytest.raises(ValueError, match="Debug mode is strictly forbidden"):
        validate_release_config(staging_config(debug=True))


def test_invalid_app_env() -> None:
    with pytest.raises(ValueError, match="Unsupported application environment"):
        validate_release_config(production_config(app_env="qa_arbitrary"))


def test_invalid_database_scheme() -> None:
    with pytest.raises(ValueError, match="Invalid database URL scheme"):
        validate_release_config(production_config(database_url="mysql://user:pass@localhost/db"))


def test_invalid_redis_scheme() -> None:
    with pytest.raises(ValueError, match="Invalid redis URL scheme"):
        validate_release_config(production_config(redis_url="memcached://localhost:11211"))
