import os
from urllib.parse import urlparse

import pytest


def database_identity(url: str) -> tuple[str, int | None, str]:
    parsed = urlparse(url)
    return (parsed.hostname or "", parsed.port, parsed.path.lstrip("/"))


def test_database_identity_parsing():
    identity = database_identity("postgresql+asyncpg://user:pass@db.internal:5432/fashx_prod")
    assert identity == ("db.internal", 5432, "fashx_prod")

    sqlite_identity = database_identity("sqlite+aiosqlite:///./fashx_local.db")
    assert sqlite_identity == ("", None, "./fashx_local.db")


def test_environment_database_identities_are_distinct():
    dev_url = "postgresql+asyncpg://dev_user:pass@db.dev.internal:5432/fashx_dev"
    staging_url = "postgresql+asyncpg://staging_user:pass@db.staging.internal:5432/fashx_staging"
    prod_url = "postgresql+asyncpg://prod_user:pass@db.prod.internal:5432/fashx_prod"

    assert database_identity(dev_url) != database_identity(staging_url)
    assert database_identity(staging_url) != database_identity(prod_url)
    assert database_identity(dev_url) != database_identity(prod_url)


def test_development_and_staging_database_are_distinct_env():
    dev = os.getenv("DEV_DATABASE_URL")
    staging = os.getenv("STAGING_DATABASE_URL")
    if not dev or not staging:
        pytest.skip("Provisioned development and staging URLs are required via environment")
    assert database_identity(dev) != database_identity(staging)


def test_staging_and_production_database_are_distinct_env():
    staging = os.getenv("STAGING_DATABASE_URL")
    production = os.getenv("PRODUCTION_DATABASE_URL")
    if not staging or not production:
        pytest.skip("Provisioned staging and production URLs are required via environment")
    assert database_identity(staging) != database_identity(production)
