import os
from urllib.parse import urlparse

import pytest

ENVIRONMENTS = {
    "dev": os.getenv("DEV_DATABASE_URL", "postgresql+asyncpg://dev_app:secret@db.dev.internal:5432/fashx_dev"),
    "staging": os.getenv(
        "STAGING_DATABASE_URL",
        "postgresql+asyncpg://staging_app:secret@db.staging.internal:5432/fashx_staging",
    ),
    "prod": os.getenv("PROD_DATABASE_URL", "postgresql+asyncpg://prod_app:secret@db.prod.internal:5432/fashx_prod"),
}


def database_identity(url: str) -> tuple[str | None, int, str]:
    parsed = urlparse(url)
    return (parsed.hostname, parsed.port or 5432, parsed.path)


@pytest.mark.parametrize(
    "first,second",
    [
        ("dev", "staging"),
        ("dev", "prod"),
        ("staging", "prod"),
    ],
)
def test_environment_database_targets_are_distinct(first: str, second: str):
    first_url = ENVIRONMENTS[first]
    second_url = ENVIRONMENTS[second]
    assert database_identity(first_url) != database_identity(second_url)


def test_custom_ports_and_host_distinction():
    dev = "postgresql+asyncpg://u:p@db.internal:5432/fashx_dev"
    staging = "postgresql+asyncpg://u:p@db.internal:5433/fashx_staging"
    assert database_identity(dev) != database_identity(staging)


def test_rds_instance_endpoint_identities_are_distinct():
    dev_rds = "postgresql+asyncpg://fashx_dev_app:secret@fashx-pg-dev.c123456789.ap-south-1.rds.amazonaws.com:5432/fashx_dev"
    staging_rds = "postgresql+asyncpg://fashx_staging_app:secret@fashx-pg-staging.c123456789.ap-south-1.rds.amazonaws.com:5432/fashx_staging"
    prod_rds = "postgresql+asyncpg://fashx_prod_app:secret@fashx-pg-prod.c123456789.ap-south-1.rds.amazonaws.com:5432/fashx_prod"

    assert database_identity(dev_rds) != database_identity(staging_rds)
    assert database_identity(staging_rds) != database_identity(prod_rds)
    assert database_identity(dev_rds) != database_identity(prod_rds)
