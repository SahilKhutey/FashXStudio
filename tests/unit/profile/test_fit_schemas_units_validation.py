"""Tests for Fit Profile Schemas, Units, and Range Validation (FITP-SCH, FITP-MAN, FITP-UNT, FITP-RNG)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from fashx.profile.fit_schemas import (
    MeasurementBatchRequest,
    MeasurementInput,
)
from fashx.profile.units import (
    ProfileUnit,
    normalize_length_to_cm,
    normalize_measurement_value,
    normalize_weight_to_kg,
)
from fashx.profile.validation import (
    MeasurementValidationStatus,
    validate_measurement,
)


def test_valid_batch_and_rejections():
    """FITP-SCH-001..005 & FITP-MAN-001..005: Schema constraints."""
    # Valid single field batch (partial profile allowed)
    batch = MeasurementBatchRequest(
        measurements=[
            MeasurementInput(field="chest", value=Decimal("96.5"), unit=ProfileUnit.CM)
        ]
    )
    assert batch.measurements[0].field == "CHEST"

    # Empty batch rejected
    with pytest.raises(ValidationError):
        MeasurementBatchRequest(measurements=[])

    # Duplicate fields in batch rejected
    with pytest.raises(ValidationError):
        MeasurementBatchRequest(
            measurements=[
                MeasurementInput(field="CHEST", value=Decimal("96"), unit=ProfileUnit.CM),
                MeasurementInput(field="chest", value=Decimal("97"), unit=ProfileUnit.CM),
            ]
        )

    # Zero, negative, excess decimal (>3 decimals), invalid unit rejected
    for bad_val in ("0", "-5", "96.1234"):
        with pytest.raises(ValidationError):
            MeasurementInput(field="CHEST", value=Decimal(bad_val), unit=ProfileUnit.CM)

    with pytest.raises(ValidationError):
        MeasurementInput(field="CHEST", value=Decimal("96"), unit="YARDS")  # type: ignore[arg-type]


def test_unit_conversions_and_type_guards():
    """FITP-UNT-001..004: Deterministic CM/MM/IN normalization and KG type enforcement."""
    assert normalize_length_to_cm(Decimal("10"), ProfileUnit.IN) == Decimal("25.40")
    assert normalize_length_to_cm(Decimal("100"), ProfileUnit.MM) == Decimal("10.00")
    assert normalize_length_to_cm(Decimal("96.5"), ProfileUnit.CM) == Decimal("96.50")
    assert normalize_weight_to_kg(Decimal("68.25"), ProfileUnit.KG) == Decimal("68.25")

    # KG supplied for CHEST -> rejected
    with pytest.raises(ValueError, match="not valid for a length measurement"):
        normalize_measurement_value("CHEST", Decimal("70"), ProfileUnit.KG)

    # CM supplied for WEIGHT -> rejected
    with pytest.raises(ValueError, match="not valid for a weight measurement"):
        normalize_measurement_value("WEIGHT", Decimal("70"), ProfileUnit.CM)


def test_measurement_range_validation_and_confirmation_flow():
    """FITP-RNG-001..004: Hard vs provisional plausibility bounds and exception confirmation."""
    # Within provisional range
    ok = validate_measurement("CHEST", Decimal("96.0"), ProfileUnit.CM)
    assert ok.validation_status == MeasurementValidationStatus.ACCEPTED
    assert ok.normalized_value == Decimal("96.00")

    # Unusual low / high triggers NEEDS_CONFIRMATION instead of silent clipping or permanent block
    low = validate_measurement("CHEST", Decimal("25.0"), ProfileUnit.CM, confirm_unusual=False)
    assert low.validation_status == MeasurementValidationStatus.NEEDS_CONFIRMATION
    assert low.message is not None

    high = validate_measurement("CHEST", Decimal("195.0"), ProfileUnit.CM, confirm_unusual=False)
    assert high.validation_status == MeasurementValidationStatus.NEEDS_CONFIRMATION

    # Confirmed unusual value proceeds under exception policy (WARNING)
    confirmed = validate_measurement("CHEST", Decimal("195.0"), ProfileUnit.CM, confirm_unusual=True)
    assert confirmed.validation_status == MeasurementValidationStatus.WARNING

    # Hard technical ceiling (> 500 CM) raises ValueError
    with pytest.raises(ValueError, match="outside technical bounds"):
        validate_measurement("CHEST", Decimal("600"), ProfileUnit.CM, confirm_unusual=True)

    # Unknown field raises ValueError
    with pytest.raises(ValueError, match="Unknown measurement field"):
        validate_measurement("ANKLE_CIRCUMFERENCE", Decimal("25"), ProfileUnit.CM)
