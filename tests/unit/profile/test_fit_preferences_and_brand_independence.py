"""Tests for Fit Preferences, Category Isolation, and Brand-Size Independence (FITP-PREF, FITP-CAT, FITP-BRD)."""

from __future__ import annotations

import pytest

from fashx.profile.preferences import (
    BrandSizeMappingError,
    ensure_no_brand_size_assumption,
    resolve_fit_preference,
    validate_category,
    validate_fit_preference,
)


def test_fit_preference_precedence_and_fallbacks():
    """FITP-PREF-001..003 & FITP-CAT-001..005: Independent category preferences & precedence."""
    # Explicit category preference wins over default
    assert (
        resolve_fit_preference(
            category="TSHIRTS",
            category_preferences={"TSHIRTS": "RELAXED"},
            default_preference="REGULAR",
        )
        == "RELAXED"
    )

    # Category without explicit override falls back to default preference
    assert (
        resolve_fit_preference(
            category="SHIRTS",
            category_preferences={"TSHIRTS": "RELAXED"},
            default_preference="REGULAR",
        )
        == "REGULAR"
    )

    # Clearing / None default resolves to NO_PREFERENCE (never forced to REGULAR)
    assert (
        resolve_fit_preference(
            category="TROUSERS",
            category_preferences={"TSHIRTS": "OVERSIZED"},
            default_preference=None,
        )
        == "NO_PREFERENCE"
    )

    # Unsupported category never inherits preferences
    assert (
        resolve_fit_preference(
            category="HATS",
            category_preferences={"TSHIRTS": "RELAXED"},
            default_preference="REGULAR",
        )
        == "NO_PREFERENCE"
    )


def test_category_and_preference_validation():
    """Reject unknown categories and invalid preference strings."""
    assert validate_category("tshirts") == "TSHIRTS"
    assert validate_fit_preference("oversized") == "OVERSIZED"

    with pytest.raises(ValueError, match="Unsupported category"):
        validate_category("SWIMWEAR")

    with pytest.raises(ValueError, match="Invalid fit preference"):
        validate_fit_preference("SUPER_SKINNY")


def test_no_brand_size_equivalence_assumed():
    """FITP-BRD-001..003: Prohibit universal brand-size conversion without verified product chart."""
    with pytest.raises(BrandSizeMappingError, match="INSUFFICIENT_DATA"):
        ensure_no_brand_size_assumption(
            has_product_chart=False,
            has_chart_basis=True,
            has_required_body_measurements=True,
        )

    with pytest.raises(BrandSizeMappingError, match="INSUFFICIENT_DATA"):
        ensure_no_brand_size_assumption(
            has_product_chart=True,
            has_chart_basis=False,
            has_required_body_measurements=True,
        )

    with pytest.raises(BrandSizeMappingError, match="INSUFFICIENT_DATA"):
        ensure_no_brand_size_assumption(
            has_product_chart=True,
            has_chart_basis=True,
            has_required_body_measurements=False,
        )

    # Allowed only when product chart, chart basis, and body measurements are all verified
    ensure_no_brand_size_assumption(
        has_product_chart=True,
        has_chart_basis=True,
        has_required_body_measurements=True,
    )
