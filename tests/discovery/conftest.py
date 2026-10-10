"""Pytest fixtures for discovery ranking evaluation."""

import pytest

from fashx.discovery.catalog_data import get_catalog_items


@pytest.fixture
def db_with_real_catalog():
    """Provide catalog database context (real or snapshot) for ranking pipeline."""
    return get_catalog_items()
