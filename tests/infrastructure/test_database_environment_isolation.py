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
