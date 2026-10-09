import pytest


def both():
    """Parametrize a repo fixture over both adapters; SQL variant is marked db."""
    return pytest.fixture(
        params=[
            pytest.param("memory"),
            pytest.param("sql", marks=pytest.mark.db),
        ]
    )
