"""Deterministic unit normalization for shopper profile measurements (Phase 08.2 - Task 8.2.4)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from enum import Enum


class ProfileUnit(str, Enum):
    """Supported input and normalized units for body measurements."""

    CM = "CM"
    MM = "MM"
    IN = "IN"
    KG = "KG"


LENGTH_UNITS = frozenset({ProfileUnit.CM, ProfileUnit.MM, ProfileUnit.IN})
CM_PRECISION = Decimal("0.01")
KG_PRECISION = Decimal("0.01")


def normalize_length_to_cm(value: Decimal, unit: ProfileUnit | str) -> Decimal:
    """Normalize linear or circumference body measurements deterministically to CM."""
    if not value.is_finite() or value <= 0:
        raise ValueError("Value must be positive and finite")

    unit_enum = unit if isinstance(unit, ProfileUnit) else ProfileUnit(str(unit).strip().upper())
    if unit_enum == ProfileUnit.CM:
        result = value
    elif unit_enum == ProfileUnit.MM:
        result = value / Decimal("10")
    elif unit_enum == ProfileUnit.IN:
        result = value * Decimal("2.54")
    else:
        raise ValueError("Unit is not valid for a length measurement")

    return result.quantize(CM_PRECISION, rounding=ROUND_HALF_UP)


def normalize_weight_to_kg(value: Decimal, unit: ProfileUnit | str) -> Decimal:
    """Normalize weight measurements deterministically to KG."""
    if not value.is_finite() or value <= 0:
        raise ValueError("Weight must be positive and finite")

    unit_enum = unit if isinstance(unit, ProfileUnit) else ProfileUnit(str(unit).strip().upper())
    if unit_enum != ProfileUnit.KG:
        raise ValueError("Unit is not valid for a weight measurement")

    return value.quantize(KG_PRECISION, rounding=ROUND_HALF_UP)


def normalize_measurement_value(
    field_code: str,
    value: Decimal,
    unit: ProfileUnit | str,
) -> tuple[Decimal, ProfileUnit]:
    """Normalize a body measurement according to its field type (length/circumference vs weight)."""
    norm_field = field_code.strip().upper()
    if norm_field == "WEIGHT":
        return normalize_weight_to_kg(value, unit), ProfileUnit.KG
    return normalize_length_to_cm(value, unit), ProfileUnit.CM


# Backward-compatible helpers from Phase 04/05 profile onboarding
def inches_to_cm(inches: Decimal | float | int) -> Decimal:
    """Convert inches to centimeters (1 decimal place)."""
    val = Decimal(str(inches))
    if val <= 0:
        raise ValueError("Height must be positive")
    return (val * Decimal("2.54")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def feet_inches_to_cm(feet: int, inches: Decimal | float | int = 0) -> Decimal:
    """Convert feet and inches to centimeters (1 decimal place)."""
    f = Decimal(str(feet))
    i = Decimal(str(inches))
    if f < 0 or i < 0:
        raise ValueError("Feet and inches must be non-negative")
    if i >= 12:
        raise ValueError("Inches must be less than 12")
    total_inches = (f * Decimal("12")) + i
    if total_inches <= 0:
        raise ValueError("Total height must be greater than zero")
    return (total_inches * Decimal("2.54")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def pounds_to_kg(pounds: Decimal | float | int) -> Decimal:
    """Convert pounds (lb) to kilograms (kg, 1 decimal place)."""
    val = Decimal(str(pounds))
    if val <= 0:
        raise ValueError("Weight must be positive")
    return (val * Decimal("0.45359237")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
