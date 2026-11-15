from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def inches_to_cm(inches: Decimal | float | int) -> Decimal:
    """Convert inches to centimeters."""
    val = Decimal(str(inches))
    if val <= 0:
        raise ValueError("Height must be positive")
    return (val * Decimal("2.54")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def feet_inches_to_cm(feet: int, inches: Decimal | float | int = 0) -> Decimal:
    """Convert feet and inches to centimeters."""
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
    """Convert pounds (lb) to kilograms (kg)."""
    val = Decimal(str(pounds))
    if val <= 0:
        raise ValueError("Weight must be positive")
    return (val * Decimal("0.45359237")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
