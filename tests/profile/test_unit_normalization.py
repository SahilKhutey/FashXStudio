from __future__ import annotations

from decimal import Decimal

import pytest

from fashx.profile.units import (
    feet_inches_to_cm,
    inches_to_cm,
    pounds_to_kg,
)


def test_inches_to_cm_standard_values():
    """PROF-001: Inches to cm converts accurately with Decimal precision."""
    # 70 inches = 177.8 cm
    assert inches_to_cm(70) == Decimal("177.8")
    assert inches_to_cm(Decimal("70")) == Decimal("177.8")
    assert inches_to_cm(68.5) == Decimal("174.0")


def test_feet_inches_to_cm_standard_values():
    """PROF-002: Feet & inches to cm converts accurately."""
    # 5 feet 10 inches = 70 inches = 177.8 cm
    assert feet_inches_to_cm(5, 10) == Decimal("177.8")
    # 5 feet 0 inches = 60 inches = 152.4 cm
    assert feet_inches_to_cm(5, 0) == Decimal("152.4")
    # 6 feet 2 inches = 74 inches = 188.0 cm
    assert feet_inches_to_cm(6, 2) == Decimal("188.0")


def test_pounds_to_kg_standard_values():
    """PROF-003: Pounds to kg converts accurately."""
    # 154 lbs ~= 69.9 kg (154 * 0.45359237 = 69.85322498 -> 69.9)
    assert pounds_to_kg(154) == Decimal("69.9")
    # 220 lbs ~= 99.8 kg
    assert pounds_to_kg(220) == Decimal("99.8")


def test_unit_conversion_invalid_inputs():
    """PROF-004: Invalid negative or extreme values fail validation."""
    with pytest.raises(ValueError, match="Height must be positive"):
        inches_to_cm(-5)

    with pytest.raises(ValueError, match="Feet and inches must be non-negative"):
        feet_inches_to_cm(-1, 5)

    with pytest.raises(ValueError, match="Inches must be less than 12"):
        feet_inches_to_cm(5, 13)

    with pytest.raises(ValueError, match="Weight must be positive"):
        pounds_to_kg(-10)
