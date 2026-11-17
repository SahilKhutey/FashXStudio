from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from fashx.profile.schemas import (
    ColorPreference,
    PreferredFit,
    ProductCategory,
    ShopperProfileCreate,
    ShopperProfileUpdate,
    ShoppingBudget,
    ShoppingIntent,
    ShoppingPreferences,
    SizeSystem,
    StylePreference,
)


def test_height_range_validation():
    """PROF-005: Height must be between 80.0 cm and 250.0 cm."""
    # Valid boundaries
    p1 = ShopperProfileCreate(height_cm=Decimal("80.0"))
    assert p1.height_cm == Decimal("80.0")

    p2 = ShopperProfileCreate(height_cm=Decimal("250.0"))
    assert p2.height_cm == Decimal("250.0")

    # Invalid below 80
    with pytest.raises(ValidationError):
        ShopperProfileCreate(height_cm=Decimal("79.9"))

    # Invalid above 250
    with pytest.raises(ValidationError):
        ShopperProfileCreate(height_cm=Decimal("250.1"))


def test_weight_range_validation():
    """PROF-006: Weight must be between 20.0 kg and 400.0 kg."""
    # Valid boundaries
    p1 = ShopperProfileCreate(weight_kg=Decimal("20.0"))
    assert p1.weight_kg == Decimal("20.0")

    p2 = ShopperProfileCreate(weight_kg=Decimal("400.0"))
    assert p2.weight_kg == Decimal("400.0")

    # Invalid below 20
    with pytest.raises(ValidationError):
        ShopperProfileCreate(weight_kg=Decimal("19.9"))

    # Invalid above 400
    with pytest.raises(ValidationError):
        ShopperProfileCreate(weight_kg=Decimal("400.1"))


def test_physical_attributes_optional():
    """PROF-007: All physical attributes are completely optional."""
    p = ShopperProfileCreate()
    assert p.height_cm is None
    assert p.weight_kg is None
    assert p.preferred_size_system is None
    assert p.preferred_fit is None
    assert p.style_preferences == []
    assert p.preferred_colors == []
    assert p.product_categories == []


def test_controlled_enums_validation():
    """PROF-008: Size systems and preferred fit enforce strict enum validation."""
    # Valid
    p = ShopperProfileCreate(
        preferred_size_system=SizeSystem.IN,
        preferred_fit=PreferredFit.SLIM,
    )
    assert p.preferred_size_system == SizeSystem.IN
    assert p.preferred_fit == PreferredFit.SLIM

    # Invalid size system
    with pytest.raises(ValidationError):
        ShopperProfileCreate(preferred_size_system="INVALID_SYS")  # type: ignore[arg-type]

    # Invalid fit
    with pytest.raises(ValidationError):
        ShopperProfileCreate(preferred_fit="TIGHT")  # type: ignore[arg-type]


def test_style_and_color_preferences_validation():
    """PROF-009: Style, color, and category enums validation."""
    p = ShopperProfileCreate(
        style_preferences=[StylePreference.CASUAL, StylePreference.STREETWEAR],
        preferred_colors=[ColorPreference.NAVY, ColorPreference.BLACK],
        product_categories=[ProductCategory.TOPS, ProductCategory.BOTTOMS],
    )
    assert len(p.style_preferences) == 2
    assert ColorPreference.NAVY in p.preferred_colors
    assert ProductCategory.TOPS in p.product_categories

    with pytest.raises(ValidationError):
        ShopperProfileCreate(style_preferences=["CYBERPUNK"])  # type: ignore[list-item]


def test_shopping_preferences_budget_validation():
    """PROF-010: Budget validation ensures min <= max and non-negative."""
    # Valid budget
    pref = ShoppingPreferences(
        budget=ShoppingBudget(min=Decimal("500"), max=Decimal("2500"), currency="INR"),
        shopping_intents=[ShoppingIntent.WORKWEAR, ShoppingIntent.EVERYDAY_WEAR],
    )
    assert pref.budget.min == Decimal("500")

    # Invalid budget_min > budget_max
    with pytest.raises(
        ValidationError, match="Minimum budget cannot be greater than maximum budget"
    ):
        ShoppingPreferences(budget=ShoppingBudget(min=Decimal("5000"), max=Decimal("1000")))

    # Invalid negative budget
    with pytest.raises(ValidationError):
        ShoppingPreferences(budget=ShoppingBudget(min=Decimal("-100")))


def test_mass_assignment_protection():
    """PROF-011: Client-supplied user_id, version, or created_at is strictly rejected."""
    # Extra fields forbidden on create
    with pytest.raises(ValidationError):
        ShopperProfileCreate.model_validate(
            {
                "user_id": "00000000-0000-0000-0000-000000000001",
                "height_cm": 175,
            }
        )

    with pytest.raises(ValidationError):
        ShopperProfileCreate.model_validate(
            {
                "version": 5,
                "height_cm": 175,
            }
        )

    # Extra fields forbidden on update
    with pytest.raises(ValidationError):
        ShopperProfileUpdate.model_validate(
            {
                "user_id": "00000000-0000-0000-0000-000000000001",
                "height_cm": 175,
            }
        )
