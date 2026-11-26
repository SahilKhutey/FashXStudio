"""Tests for Size Chart Schemas (SZ-SCH-001 - SZ-SCH-004)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from fashx.catalog.size_charts.enums import (
    AvailabilityStatus,
    MappingStatus,
    MeasurementBasis,
    MeasurementUnit,
)
from fashx.catalog.size_charts.schemas import (
    ProductVariantAvailability,
    SizeChartRevisionCreate,
    SizeChartRow,
    SizeChartUnavailableResponse,
    SizeMeasurement,
    SizeSystemRef,
    SourceProvenance,
    VariantStockItem,
)


def test_valid_size_chart_revision_create():
    """SZ-SCH-001: Validate valid SizeChartRevisionCreate payload."""
    payload = SizeChartRevisionCreate(
        size_system=SizeSystemRef(
            code="INTL_ALPHA",
            system_type="REGIONAL_STANDARD",
            display_name="International Alpha",
            mapping_status=MappingStatus.NATIVE,
        ),
        measurement_basis=MeasurementBasis.GARMENT,
        default_unit=MeasurementUnit.CM,
        source=SourceProvenance(
            source_id="MERCHANT_PORTAL",
            source_revision="v2026.1",
            retrieved_at=datetime.now(UTC),
            verified_at=datetime.now(UTC),
        ),
        rows=[
            SizeChartRow(
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
            SizeChartRow(
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
        ],
    )
    assert len(payload.rows) == 2
    assert payload.rows[0].merchant_size == "S"
    assert payload.rows[1].measurements[0].field_code == "CHEST"


def test_reject_duplicate_size_labels():
    """SZ-SCH-002: Reject payload with duplicate size labels in same chart."""
    with pytest.raises(ValueError, match="Duplicate size labels"):
        SizeChartRevisionCreate(
            size_system=SizeSystemRef(
                code="INTL_ALPHA",
                system_type="REGIONAL_STANDARD",
                display_name="International Alpha",
            ),
            measurement_basis=MeasurementBasis.GARMENT,
            default_unit=MeasurementUnit.CM,
            source=SourceProvenance(
                source_id="TEST",
                retrieved_at=datetime.now(UTC),
            ),
            rows=[
                SizeChartRow(
                    merchant_size="M",
                    measurements=[
                        SizeMeasurement(
                            field_code="CHEST",
                            original_value=Decimal("98.00"),
                            original_unit=MeasurementUnit.CM,
                        )
                    ],
                ),
                SizeChartRow(
                    merchant_size="m",  # duplicate case-insensitively
                    measurements=[
                        SizeMeasurement(
                            field_code="CHEST",
                            original_value=Decimal("100.00"),
                            original_unit=MeasurementUnit.CM,
                        )
                    ],
                ),
            ],
        )


def test_reject_duplicate_measurement_fields_in_row():
    """SZ-SCH-003: Reject payload with duplicate measurement fields in same row."""
    with pytest.raises(ValueError, match="Duplicate measurement field"):
        SizeChartRow(
            merchant_size="L",
            measurements=[
                SizeMeasurement(
                    field_code="CHEST",
                    original_value=Decimal("104.00"),
                    original_unit=MeasurementUnit.CM,
                ),
                SizeMeasurement(
                    field_code="CHEST",
                    original_value=Decimal("106.00"),
                    original_unit=MeasurementUnit.CM,
                ),
            ],
        )


def test_enforce_strictly_positive_measurements():
    """SZ-SCH-004: Enforce strictly positive measurement values."""
    with pytest.raises(ValidationError):
        SizeMeasurement(
            field_code="CHEST",
            original_value=Decimal("-10.00"),
            original_unit=MeasurementUnit.CM,
        )

    with pytest.raises(ValidationError):
        SizeMeasurement(
            field_code="CHEST",
            original_value=Decimal("0.00"),
            original_unit=MeasurementUnit.CM,
        )


def test_unavailable_response_contract():
    """Verify explicit unavailable response."""
    p_id = str(uuid4())
    resp = SizeChartUnavailableResponse(product_id=p_id)
    assert resp.product_id == p_id
    assert resp.status == "UNAVAILABLE"
    assert "not provided" in resp.message.lower()


def test_variant_availability_contract():
    """Verify ProductVariantAvailability contract."""
    p_id = uuid4()
    item = VariantStockItem(
        variant_id="var_01",
        size_label="M",
        colour_label="Blue",
        sku="SKU-BLU-M",
        status=AvailabilityStatus.IN_STOCK,
        is_stale=False,
        observed_at=datetime.now(UTC),
    )
    avail = ProductVariantAvailability(
        merchant_product_id=p_id,
        overall_status=AvailabilityStatus.IN_STOCK,
        variants=[item],
        last_checked_at=datetime.now(UTC),
    )
    assert avail.overall_status == AvailabilityStatus.IN_STOCK
    assert len(avail.variants) == 1
    assert avail.variants[0].size_label == "M"
