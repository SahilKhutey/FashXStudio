"""Tests for Category Measurement Policies and Definitions (FITP-REQ-001..004, FITP-GUI-001..002)."""

from __future__ import annotations

import pytest

from fashx.profile.fit_policy import (
    CATEGORY_POLICIES,
    UnsupportedCategoryPolicyError,
    evaluate_category_readiness,
    missing_required_measurements,
)
from fashx.profile.measurement_definitions import (
    MEASUREMENT_DEFINITIONS,
    get_measurement_definition,
    list_measurement_definitions,
)


def test_tshirt_requires_chest_only():
    """FITP-REQ-002 / FITP-REQ-004: T-shirts require CHEST; optional fields do not block readiness."""
    missing = missing_required_measurements("TSHIRTS", set())
    assert missing == ["CHEST"]

    missing_after_chest = missing_required_measurements("TSHIRTS", {"CHEST"})
    assert missing_after_chest == []

    readiness = evaluate_category_readiness("TSHIRTS", {"CHEST"})
    assert readiness.status == "READY"
    assert "SHOULDER" not in readiness.missing_fields


def test_trouser_requires_waist_and_hip():
    """FITP-REQ-003: Trousers require WAIST and HIP."""
    missing_both = missing_required_measurements("TROUSERS", set())
    assert missing_both == ["WAIST", "HIP"]

    missing_hip = missing_required_measurements("TROUSERS", {"WAIST"})
    assert missing_hip == ["HIP"]

    ready = evaluate_category_readiness("TROUSERS", {"WAIST", "HIP"})
    assert ready.status == "READY"


def test_unsupported_category_does_not_guess_or_inherit():
    """FITP-GUI-002: Unsupported categories never silently inherit another category's requirements."""
    with pytest.raises(UnsupportedCategoryPolicyError):
        missing_required_measurements("SUNGLASSES", set())

    readiness = evaluate_category_readiness("SUNGLASSES", {"CHEST", "WAIST"})
    assert readiness.status == "UNSUPPORTED_CATEGORY"
    assert readiness.policy_version is None


def test_browse_without_measurements_profile_incomplete():
    """FITP-REQ-001: Missing measurements report category readiness without blocking profile."""
    for cat in CATEGORY_POLICIES:
        r = evaluate_category_readiness(cat, set())
        assert r.status == "MISSING_REQUIRED_MEASUREMENTS"
        assert len(r.missing_fields) >= 1


def test_measurement_definitions_provide_shopper_guidance():
    """FITP-GUI-001: Every registered measurement includes plain-language explanation and tape guidance."""
    defs = list_measurement_definitions()
    assert len(defs) == len(MEASUREMENT_DEFINITIONS)
    for d in defs:
        assert d.explanation.strip()
        assert d.tape_positioning.strip()
        assert d.how_to_hold.strip()
        assert d.example_input.strip()

    chest = get_measurement_definition("chest")
    assert chest is not None
    assert chest.code == "CHEST"
    assert "TSHIRTS" in chest.supported_categories

    weight = get_measurement_definition("WEIGHT")
    assert weight is not None
    assert weight.is_optional_contextual is True
