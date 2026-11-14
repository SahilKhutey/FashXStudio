from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class ReleaseConfig:
    app_env: str
    auth_mode: str
    database_url: str
    redis_url: str
    storage_backend: str
    tryon_provider: str
    cors_origins: list[str]
    debug: bool


def validate_release_config(config: ReleaseConfig) -> None:
    """Validate release configuration against stage-appropriate security invariants."""
    allowed_envs = {"development", "staging", "production"}
    if config.app_env not in allowed_envs:
        raise ValueError(
            f"Unsupported application environment: {config.app_env}. Allowed: {allowed_envs}"
        )

    # Validate database URL scheme
    parsed_db = urlparse(config.database_url)
    if not (parsed_db.scheme.startswith("postgresql") or parsed_db.scheme.startswith("postgres") or parsed_db.scheme.startswith("sqlite")):
        raise ValueError(f"Invalid database URL scheme: {parsed_db.scheme}")

    # Validate redis URL scheme
    parsed_redis = urlparse(config.redis_url)
    if parsed_redis.scheme not in {"redis", "rediss"}:
        raise ValueError(f"Invalid redis URL scheme: {parsed_redis.scheme}")

    if config.app_env in {"staging", "production"}:
        if config.debug:
            raise ValueError(f"Debug mode is strictly forbidden in {config.app_env}")

        if config.auth_mode != "jwks":
            raise ValueError(
                f"{config.app_env.capitalize()} requires JWKS authentication (got: {config.auth_mode})"
            )

        if config.storage_backend != "s3":
            raise ValueError(
                f"{config.app_env.capitalize()} requires private object storage (storage_backend=s3)"
            )

        if not config.cors_origins:
            raise ValueError(f"{config.app_env.capitalize()} CORS origins cannot be empty")

        for origin in config.cors_origins:
            if origin == "*":
                raise ValueError(f"Wildcard CORS origin is forbidden in {config.app_env}")
            parsed = urlparse(origin)
            if parsed.scheme not in {"https", "http"} or not parsed.netloc:
                raise ValueError(f"Invalid CORS origin format: {origin}")
            if config.app_env == "production" and parsed.scheme != "https":
                raise ValueError(
                    f"Production CORS origins must use HTTPS (got: {origin})"
                )

        if not (config.database_url.startswith("postgresql") or config.database_url.startswith("postgres")):
            raise ValueError(
                f"{config.app_env.capitalize()} requires PostgreSQL database (got: {config.database_url})"
            )

    if config.app_env == "production":
        if parsed_redis.scheme != "rediss":
            raise ValueError(
                f"Production requires TLS-encrypted Redis connection (rediss://, got: {config.redis_url})"
            )
        if config.tryon_provider == "mock":
            raise ValueError("Production requires approved real tryon_provider (mock forbidden)")
