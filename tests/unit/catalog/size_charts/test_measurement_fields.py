"""Tests for Measurement Field Definitions (SZ-FLD-001 - SZ-FLD-002)."""

from __future__ import annotations

from fashx.catalog.size_charts.measurement_fields import (
    FIELD_DEFINITIONS,
    get_field_definition,
    is_field_valid_for_category,
)


def test_standard_fields_registered():
    """SZ-FLD-001: Verify all standard measurement fields are registered."""
    expected_fields = [
        "CHEST",
        "BUST",
        "WAIST",
        "HIP",
        "LENGTH",
        "SHOULDER",
        "SLEEVE_LENGTH",
        "INSEAM",
        "OUTSEAM",
        "THIGH",
        "RISE",
        "NECK",
    ]
    for field in expected_fields:
        assert field in FIELD_DEFINITIONS
        definition = get_field_definition(field)
        assert definition is not None
        assert definition.code == field
        assert definition.minimum_cm > 0
        assert definition.maximum_cm > definition.minimum_cm


def test_field_physical_range_bounds():
    """SZ-FLD-002: Verify physical plausible range limits for fields."""
    chest = FIELD_DEFINITIONS["CHEST"]
    assert chest.minimum_cm == 40.0
    assert chest.maximum_cm == 200.0

    waist = FIELD_DEFINITIONS["WAIST"]
    assert waist.minimum_cm == 30.0
    assert waist.maximum_cm == 180.0

    inseam = FIELD_DEFINITIONS["INSEAM"]
    assert inseam.minimum_cm == 20.0
    assert inseam.maximum_cm == 120.0


def test_category_eligibility():
    """Verify category compatibility rules."""
    # Inseam is only valid for bottoms
    assert is_field_valid_for_category("INSEAM", "BOTTOMS") is True
    assert is_field_valid_for_category("INSEAM", "TOPS") is False
    assert is_field_valid_for_category("INSEAM", "DRESSES") is False

    # Chest is valid for tops, dresses, outerwear, and general
    assert is_field_valid_for_category("CHEST", "TOPS") is True
    assert is_field_valid_for_category("CHEST", "DRESSES") is True
    assert is_field_valid_for_category("CHEST", "GENERAL") is True

    # Length is universal
    assert is_field_valid_for_category("LENGTH", "TOPS") is True
    assert is_field_valid_for_category("LENGTH", "BOTTOMS") is True
    assert is_field_valid_for_category("LENGTH", "DRESSES") is True
