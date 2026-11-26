"""Tests for Sizing System Registry (SZ-SYS-001 - SZ-SYS-003)."""

from __future__ import annotations

from fashx.catalog.size_charts.size_systems import (
    SYSTEMS,
    map_size_label,
    normalize_size_label,
    register_size_system,
)


def test_standard_sizing_systems_registered():
    """SZ-SYS-001: Verify standard regional and category sizing systems are registered."""
    assert "INTL_ALPHA" in SYSTEMS
    assert "US_NUMERIC_WOMEN" in SYSTEMS
    assert "US_NUMERIC_MEN" in SYSTEMS
    assert "UK_NUMERIC" in SYSTEMS
    assert "EU_NUMERIC" in SYSTEMS
    assert "WAIST_INCHES" in SYSTEMS
    assert "COLLAR_INCHES" in SYSTEMS
    assert "INDIA_ALPHA" in SYSTEMS
    assert "ETHNIC_INDIA" in SYSTEMS

    intl = SYSTEMS["INTL_ALPHA"]
    assert "M" in intl.labels
    assert "XL" in intl.labels
    assert intl.market == "GLOBAL"

    ethnic = SYSTEMS["ETHNIC_INDIA"]
    assert "38" in ethnic.labels
    assert ethnic.category == "ETHNIC"


def test_refuse_unverified_system_conversions():
    """SZ-SYS-002: Refuse unverified conversions between arbitrary systems."""
    # US_NUMERIC_MEN to INTL_ALPHA is not a 1:1 verified mapping
    mapped = map_size_label("40", "US_NUMERIC_MEN", "INTL_ALPHA")
    assert mapped is None

    # Unknown systems return None
    mapped = map_size_label("M", "UNKNOWN_SYSTEM", "INTL_ALPHA")
    assert mapped is None


def test_verified_mapping_when_explicitly_defined():
    """Verify conversion succeeds when verified mapping is defined."""
    # UK_NUMERIC to US_NUMERIC_WOMEN (UK 10 -> US 6)
    mapped = map_size_label("10", "UK_NUMERIC", "US_NUMERIC_WOMEN")
    assert mapped == "6"

    mapped_back = map_size_label("6", "US_NUMERIC_WOMEN", "UK_NUMERIC")
    assert mapped_back == "10"


def test_normalize_size_label():
    """SZ-SYS-003: Verify size label normalization."""
    assert normalize_size_label("  m  ") == "M"
    assert normalize_size_label("xl") == "XL"
    assert normalize_size_label("  34-36  ") == "34-36"
    assert normalize_size_label("2x-large") == "2X-LARGE"


def test_register_custom_size_system():
    """Verify custom merchant size system registration."""
    register_size_system(
        code="MERCHANT_ACME_ALPHA",
        system_type="MERCHANT_PROPRIETARY",
        labels=["1", "2", "3", "4"],
        category="TOPS",
        market="US",
        display_name="Acme Custom 1-4",
    )
    assert "MERCHANT_ACME_ALPHA" in SYSTEMS
    acme = SYSTEMS["MERCHANT_ACME_ALPHA"]
    assert list(acme.labels) == ["1", "2", "3", "4"]
    assert acme.system_type == "MERCHANT_PROPRIETARY"
