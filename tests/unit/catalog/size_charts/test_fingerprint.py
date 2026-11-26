"""Tests for Canonical Fingerprinting (SZ-FPT-001 - SZ-FPT-002)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fashx.catalog.size_charts.enums import MeasurementBasis, MeasurementUnit
from fashx.catalog.size_charts.fingerprint import compute_size_chart_fingerprint
from fashx.catalog.size_charts.schemas import (
    SizeChartRevisionCreate,
    SizeChartRow,
    SizeMeasurement,
    SizeSystemRef,
    SourceProvenance,
)


def _build_test_chart(retrieved_time: datetime, row_order: list[str]) -> SizeChartRevisionCreate:
    all_rows = {
        "S": SizeChartRow(
            merchant_size="S",
            sort_order=0,
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
        "M": SizeChartRow(
            merchant_size="M",
            sort_order=1,
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
    }

    return SizeChartRevisionCreate(
        size_system=SizeSystemRef(
            code="INTL_ALPHA",
            system_type="REGIONAL_STANDARD",
            display_name="International Alpha",
        ),
        measurement_basis=MeasurementBasis.GARMENT,
        default_unit=MeasurementUnit.CM,
        source=SourceProvenance(
            source_id="MERCHANT_FEED",
            retrieved_at=retrieved_time,
        ),
        rows=[all_rows[label] for label in row_order],
    )


def test_fingerprint_excludes_volatile_timestamps():
    """SZ-FPT-001: Fingerprint is identical despite different retrieval timestamps."""
    time1 = datetime.now(UTC)
    time2 = time1 + timedelta(days=5)

    chart1 = _build_test_chart(time1, ["S", "M"])
    chart2 = _build_test_chart(time2, ["S", "M"])

    fp1 = compute_size_chart_fingerprint(chart1)
    fp2 = compute_size_chart_fingerprint(chart2)

    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-256 hex string


def test_fingerprint_order_invariance():
    """SZ-FPT-002: Identical payloads with different row order produce same fingerprint."""
    now = datetime.now(UTC)
    chart_sm = _build_test_chart(now, ["S", "M"])
    chart_ms = _build_test_chart(now, ["M", "S"])

    fp_sm = compute_size_chart_fingerprint(chart_sm)
    fp_ms = compute_size_chart_fingerprint(chart_ms)

    assert fp_sm == fp_ms


def test_fingerprint_changes_when_measurement_changes():
    """Fingerprint diverges when dimension values change."""
    now = datetime.now(UTC)
    chart1 = _build_test_chart(now, ["S", "M"])
    chart2 = _build_test_chart(now, ["S", "M"])
    chart2.rows[1].measurements[0].original_value = Decimal("99.00")  # Chest 98 -> 99

    fp1 = compute_size_chart_fingerprint(chart1)
    fp2 = compute_size_chart_fingerprint(chart2)

    assert fp1 != fp2
