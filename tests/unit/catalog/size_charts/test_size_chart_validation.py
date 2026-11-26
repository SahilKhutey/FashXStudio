"""Tests for Size Chart Validation Service (SZ-VAL-001 - SZ-VAL-004)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from fashx.catalog.size_charts.enums import MeasurementBasis, MeasurementUnit
from fashx.catalog.size_charts.schemas import (
    SizeChartRevisionCreate,
    SizeChartRow,
    SizeMeasurement,
    SizeSystemRef,
    SourceProvenance,
)
from fashx.catalog.size_charts.validation import chart_is_publishable, validate_chart


def _make_valid_payload() -> SizeChartRevisionCreate:
    return SizeChartRevisionCreate(
        size_system=SizeSystemRef(
            code="INTL_ALPHA",
            system_type="REGIONAL_STANDARD",
            display_name="International Alpha",
        ),
        measurement_basis=MeasurementBasis.GARMENT,
        default_unit=MeasurementUnit.CM,
        source=SourceProvenance(
            source_id="MERCHANT_API",
            retrieved_at=datetime.now(UTC),
        ),
        rows=[
            SizeChartRow(
                merchant_size="S",
                measurements=[
                    SizeMeasurement(
                        field_code="CHEST",
                        original_value=Decimal("92.00"),
                        original_unit=MeasurementUnit.CM,
                    ),
                    SizeMeasurement(
                        field_code="LENGTH",
                        original_value=Decimal("68.00"),
                        original_unit=MeasurementUnit.CM,
                    ),
                ],
            ),
            SizeChartRow(
                merchant_size="M",
                measurements=[
                    SizeMeasurement(
                        field_code="CHEST",
                        original_value=Decimal("98.00"),
                        original_unit=MeasurementUnit.CM,
                    ),
                    SizeMeasurement(
                        field_code="LENGTH",
                        original_value=Decimal("70.00"),
                        original_unit=MeasurementUnit.CM,
                    ),
                ],
            ),
        ],
    )


def test_valid_payload_passes_validation():
    payload = _make_valid_payload()
    result = validate_chart(payload, garment_category="TOPS")
    assert result.is_valid is True
    assert len(result.errors) == 0
    assert chart_is_publishable(result) is True


def test_reject_unregistered_measurement_fields():
    """SZ-VAL-001: Reject unknown measurement field codes."""
    payload = _make_valid_payload()
    payload.rows[0].measurements.append(
        SizeMeasurement(
            field_code="INVALID_MYSTERY_FIELD",
            original_value=Decimal("50.00"),
            original_unit=MeasurementUnit.CM,
        )
    )
    result = validate_chart(payload, garment_category="TOPS")
    assert result.is_valid is False
    assert any(e.code == "UNKNOWN_FIELD" for e in result.errors)
    assert chart_is_publishable(result) is False


def test_reject_category_incompatible_fields():
    """SZ-VAL-002: Reject measurements violating category compatibility."""
    payload = _make_valid_payload()
    # INSEAM on a TOP is invalid
    payload.rows[0].measurements.append(
        SizeMeasurement(
            field_code="INSEAM",
            original_value=Decimal("75.00"),
            original_unit=MeasurementUnit.CM,
        )
    )
    result = validate_chart(payload, garment_category="TOPS")
    assert result.is_valid is False
    assert any(e.code == "INCOMPATIBLE_FIELD_CATEGORY" for e in result.errors)


def test_reject_measurements_outside_range_bounds():
    """SZ-VAL-003: Reject measurements outside min/max range limits."""
    payload = _make_valid_payload()
    # Chest 300 cm exceeds maximum (200 cm)
    payload.rows[0].measurements[0].original_value = Decimal("300.00")

    result = validate_chart(payload, garment_category="TOPS")
    assert result.is_valid is False
    assert any(e.code == "MEASUREMENT_OUT_OF_BOUNDS" for e in result.errors)


def test_warn_on_non_monotonic_progression():
    """SZ-VAL-004: Generate warning on non-monotonic size progression."""
    payload = _make_valid_payload()
    # Size S chest is 92, Size M chest is set to 80 (smaller than S)
    payload.rows[1].measurements[0].original_value = Decimal("80.00")

    result = validate_chart(payload, garment_category="TOPS")
    # Warnings do not block publishing
    assert result.is_valid is True
    assert chart_is_publishable(result) is True
    assert len(result.warnings) > 0
    assert any("smaller than" in w.message for w in result.warnings)
