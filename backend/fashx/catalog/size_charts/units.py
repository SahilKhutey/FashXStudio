"""Measurement unit normalization service for Phase 08.1."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from .enums import MeasurementUnit

CM_PRECISION = Decimal("0.01")
INCH_TO_CM = Decimal("2.54")
MM_TO_CM = Decimal("0.1")


def normalize_to_cm(
    value: Decimal | float | int | str,
    unit: MeasurementUnit | str,
) -> Decimal:
    """Normalize a linear garment or body measurement to centimeters with decimal precision.

    Formulas:
    - 1 inch = 2.54 cm
    - 1 cm = 10 mm (1 mm = 0.1 cm)
    - Normalized CM is rounded to 2 decimal places using ROUND_HALF_UP.

    Invariants:
    1. Value must be finite and strictly positive (> 0).
    2. Unsupported units raise ValueError.
    3. Output is always a Decimal with 2 decimal places.
    """
    if not isinstance(value, Decimal):
        try:
            val_dec = Decimal(str(value))
        except Exception as exc:
            raise ValueError(f"Invalid numeric measurement: {value}") from exc
    else:
        val_dec = value

    if not val_dec.is_finite() or val_dec <= 0:
        raise ValueError("Measurement must be a positive finite value")

    # Handle string or enum unit
    unit_str = unit.value if isinstance(unit, MeasurementUnit) else str(unit).upper()

    if unit_str in (MeasurementUnit.CM.value, "CENTIMETERS", "CENTIMETRES"):
        result = val_dec
    elif unit_str in (MeasurementUnit.MM.value, "MILLIMETERS", "MILLIMETRES"):
        result = val_dec * MM_TO_CM
    elif unit_str in (MeasurementUnit.IN.value, MeasurementUnit.INCH.value, "INCHES"):
        result = val_dec * INCH_TO_CM
    else:
        raise ValueError(f"Unsupported measurement unit: {unit}")

    return result.quantize(CM_PRECISION, rounding=ROUND_HALF_UP)
