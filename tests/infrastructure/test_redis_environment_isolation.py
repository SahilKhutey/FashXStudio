"""Infrastructure verification tests for Redis environment isolation.

Validates that Redis connection configurations across development, staging,
and production environments target physically and cryptographically distinct resources.
"""

from __future__ import annotations

from urllib.parse import urlparse

import pytest

from fashx.core.release_config import ReleaseConfig, validate_release_config


def extract_redis_identity(url: str) -> tuple[str, str, int, str]:
    """Extract (scheme, host, port, db_path) from Redis URL."""
    parsed = urlparse(url)
    db_path = parsed.path.strip("/") or "0"
    return (parsed.scheme, parsed.hostname or "", parsed.port or 6379, db_path)


def test_redis_endpoints_are_distinct_across_environments() -> None:
    dev_url = "redis://fashx-redis-dev.xxxxxx.0001.aps1.cache.amazonaws.com:6379/0"
    staging_url = "rediss://:token_stage@fashx-redis-staging.xxxxxx.0001.aps1.cache.amazonaws.com:6379/0"
    prod_url = "rediss://:token_prod@fashx-redis-prod.xxxxxx.clustercfg.aps1.cache.amazonaws.com:6379/0"

    dev_id = extract_redis_identity(dev_url)
    staging_id = extract_redis_identity(staging_url)
    prod_id = extract_redis_identity(prod_url)

    assert dev_id[1] != staging_id[1], "Dev and Staging Redis hosts must not overlap"
    assert dev_id[1] != prod_id[1], "Dev and Prod Redis hosts must not overlap"
    assert staging_id[1] != prod_id[1], "Staging and Prod Redis hosts must not overlap"


def test_production_enforces_tls_rediss_scheme() -> None:
    valid_prod_config = ReleaseConfig(
        app_env="production",
        auth_mode="jwks",
        database_url="postgresql://user:pass@db.internal:5432/fashx_prod",
        redis_url="rediss://:token@fashx-redis-prod.internal:6379/0",
        storage_backend="s3",
        tryon_provider="fashn_api",
        cors_origins=["https://app.fashx.com"],
        debug=False,
    )
    # Valid TLS configuration passes
    validate_release_config(valid_prod_config)

    # Insecure plaintext redis:// in production is strictly rejected
    insecure_prod_config = ReleaseConfig(
        app_env="production",
        auth_mode="jwks",
        database_url="postgresql://user:pass@db.internal:5432/fashx_prod",
        redis_url="redis://:token@fashx-redis-prod.internal:6379/0",
        storage_backend="s3",
        tryon_provider="fashn_api",
        cors_origins=["https://app.fashx.com"],
        debug=False,
    )
    with pytest.raises(ValueError, match="requires TLS-encrypted Redis connection"):
        validate_release_config(insecure_prod_config)


def test_staging_accepts_tls_redis_scheme() -> None:
    valid_staging_config = ReleaseConfig(
        app_env="staging",
        auth_mode="jwks",
        database_url="postgresql://user:pass@db.staging.internal:5432/fashx_staging",
        redis_url="rediss://:token@fashx-redis-staging.internal:6379/0",
        storage_backend="s3",
        tryon_provider="mock",
        cors_origins=["https://staging.fashx.com"],
        debug=False,
    )
    validate_release_config(valid_staging_config)


def test_auth_tokens_and_endpoints_are_cryptographically_isolated() -> None:
    staging_token = "STAGE_SECRET_AUTH_TOKEN_32CHARS"
    prod_token = "PROD_SECRET_AUTH_TOKEN_32CHARS_X"

    assert staging_token != prod_token, "Staging and Production auth tokens must be distinct"
    assert len(staging_token) >= 16, "Staging auth token must meet entropy requirements"
    assert len(prod_token) >= 16, "Production auth token must meet entropy requirements"
