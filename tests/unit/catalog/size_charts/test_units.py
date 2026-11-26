"""Tests for Unit Normalization (SZ-UNT-001 - SZ-UNT-003)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from fashx.catalog.size_charts.enums import MeasurementUnit
from fashx.catalog.size_charts.units import normalize_to_cm


def test_inch_to_cm_conversion():
    """SZ-UNT-001: Deterministic conversion from INCH to CM with 2.54 factor."""
    # 40 inches * 2.54 = 101.60 cm
    cm_val = normalize_to_cm(Decimal("40.0"), MeasurementUnit.INCH)
    assert cm_val == Decimal("101.60")

    # 32 inches * 2.54 = 81.28 cm
    cm_val = normalize_to_cm(Decimal("32.0"), MeasurementUnit.IN)
    assert cm_val == Decimal("81.28")


def test_round_half_up_precision():
    """SZ-UNT-002: Round Half-Up precision quantization to 0.01."""
    # 39.5 inches * 2.54 = 100.33 cm
    cm_val = normalize_to_cm(Decimal("39.5"), MeasurementUnit.INCH)
    assert cm_val == Decimal("100.33")

    # Millimeters to cm (div 10)
    cm_val = normalize_to_cm(Decimal("955"), MeasurementUnit.MM)
    assert cm_val == Decimal("95.50")

    # Already CM
    cm_val = normalize_to_cm(Decimal("100.00"), MeasurementUnit.CM)
    assert cm_val == Decimal("100.00")


def test_reject_invalid_numeric_values():
    """SZ-UNT-003: Reject negative, zero, infinite, and NaN inputs."""
    with pytest.raises(ValueError, match="positive finite"):
        normalize_to_cm(Decimal("-10.0"), MeasurementUnit.CM)

    with pytest.raises(ValueError, match="positive finite"):
        normalize_to_cm(Decimal("0.0"), MeasurementUnit.CM)

    with pytest.raises(ValueError, match="finite"):
        normalize_to_cm(Decimal("Infinity"), MeasurementUnit.CM)

    with pytest.raises(ValueError, match="finite"):
        normalize_to_cm(Decimal("NaN"), MeasurementUnit.CM)
