"""Tests for Merchant Size Charts (SIZE-001..014)."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from fashx.catalog.size_charts.schemas import (
    MeasurementBasis,
    MeasurementUnit,
    SizeChartStatus,
)
from fashx.catalog.size_charts.service import (
    SizeChartService,
    SizeChartValidationError,
)


def test_size_001_valid_merchant_chart():
    service = SizeChartService()
    rows = [
        {"merchant_size": "S", "chest": Decimal("96.0"), "length": Decimal("69.0")},
        {"merchant_size": "M", "chest": Decimal("102.0"), "length": Decimal("71.0")},
    ]
    chart = service.validate_and_normalize_chart(
        merchant_id="m_001",
        merchant_product_id="prod_123",
        merchant_name="FabIndia",
        basis="GARMENT",
        unit="CM",
        source_reference="feed_sync_2026_01",
        source_revision="rev_1",
        rows=rows,
    )
    assert chart.merchant_id == "m_001"
    assert chart.merchant_name == "FabIndia"
    assert chart.status == SizeChartStatus.VERIFIED
    assert len(chart.rows) == 2
    assert chart.rows[0].merchant_size == "S"
    assert chart.rows[0].chest == Decimal("96.0")


def test_size_002_chart_provenance_identified():
    service = SizeChartService()
    chart = service.validate_and_normalize_chart(
        merchant_id="m_002",
        merchant_product_id="prod_456",
        merchant_name="Biba",
        basis=MeasurementBasis.BODY,
        unit=MeasurementUnit.CM,
        source_reference="api_catalog_v2",
        source_revision="v2.1",
        rows=[{"merchant_size": "M", "chest": Decimal("98.0")}],
    )
    assert chart.source_reference == "api_catalog_v2"
    assert chart.source_revision == "v2.1"


def test_size_003_garment_measurement_basis_labeled():
    service = SizeChartService()
    chart = service.validate_and_normalize_chart(
        merchant_id="m_003",
        merchant_product_id="prod_789",
        merchant_name="Raymond",
        basis="GARMENT",
        unit="CM",
        source_reference="raymond_feed_v1",
        source_revision="rev_1",
        rows=[{"merchant_size": "40", "chest": Decimal("104.0")}],
    )
    assert chart.basis == MeasurementBasis.GARMENT


def test_size_004_body_measurement_basis_labeled():
    service = SizeChartService()
    chart = service.validate_and_normalize_chart(
        merchant_id="m_004",
        merchant_product_id="prod_999",
        merchant_name="H&M",
        basis="BODY",
        unit="CM",
        source_reference="hm_feed",
        source_revision="rev_2",
        rows=[{"merchant_size": "M", "chest": Decimal("96.0")}],
    )
    assert chart.basis == MeasurementBasis.BODY


def test_size_005_missing_chart_unavailable_response():
    service = SizeChartService()
    resp = service.get_unavailable_response("prod_missing_123")
    assert resp.product_id == "prod_missing_123"
    assert resp.status == "UNAVAILABLE"
    assert "not provided a verified size chart" in resp.message


def test_size_006_stale_chart_flagged():
    service = SizeChartService()
    past_date = datetime.now(UTC) - timedelta(days=120)
    chart = service.validate_and_normalize_chart(
        merchant_id="m_005",
        merchant_product_id="prod_stale",
        merchant_name="Zara",
        basis="BODY",
        unit="CM",
        source_reference="zara_feed",
        source_revision="rev_old",
        rows=[{"merchant_size": "M", "chest": Decimal("100.0")}],
        last_verified_at=past_date,
    )
    assert chart.is_stale is True
    assert chart.status == SizeChartStatus.STALE


def test_size_007_missing_source_reference_rejected():
    service = SizeChartService()
    with pytest.raises(SizeChartValidationError, match="Source reference is required"):
        service.validate_and_normalize_chart(
            merchant_id="m_006",
            merchant_product_id="prod_no_ref",
            merchant_name="BrandX",
            basis="BODY",
            unit="CM",
            source_reference="",
            source_revision="rev_1",
            rows=[{"merchant_size": "M", "chest": Decimal("100.0")}],
        )


def test_size_008_unknown_unit_rejected():
    service = SizeChartService()
    with pytest.raises(SizeChartValidationError, match="Invalid or missing measurement unit"):
        service.validate_and_normalize_chart(
            merchant_id="m_007",
            merchant_product_id="prod_bad_unit",
            merchant_name="BrandY",
            basis="BODY",
            unit="METERS",
            source_reference="feed",
            source_revision="rev_1",
            rows=[{"merchant_size": "M", "chest": Decimal("100.0")}],
        )


def test_size_009_invalid_non_positive_measurement_rejected():
    service = SizeChartService()
    with pytest.raises(SizeChartValidationError, match="non-positive measurement"):
        service.validate_and_normalize_chart(
            merchant_id="m_008",
            merchant_product_id="prod_neg",
            merchant_name="BrandZ",
            basis="GARMENT",
            unit="CM",
            source_reference="feed",
            source_revision="rev_1",
            rows=[{"merchant_size": "M", "chest": Decimal("-5.0")}],
        )


def test_size_010_duplicate_size_row_rejected():
    service = SizeChartService()
    rows = [
        {"merchant_size": "M", "chest": Decimal("100.0")},
        {"merchant_size": "M", "chest": Decimal("102.0")},
    ]
    with pytest.raises(SizeChartValidationError, match="Duplicate size row 'M'"):
        service.validate_and_normalize_chart(
            merchant_id="m_009",
            merchant_product_id="prod_dup",
            merchant_name="BrandDup",
            basis="GARMENT",
            unit="CM",
            source_reference="feed",
            source_revision="rev_1",
            rows=rows,
        )


def test_size_011_empty_rows_rejected():
    service = SizeChartService()
    with pytest.raises(SizeChartValidationError, match="must contain at least one size row"):
        service.validate_and_normalize_chart(
            merchant_id="m_010",
            merchant_product_id="prod_empty",
            merchant_name="BrandEmpty",
            basis="BODY",
            unit="CM",
            source_reference="feed",
            source_revision="rev_1",
            rows=[],
        )


def test_size_012_missing_merchant_product_id_rejected():
    service = SizeChartService()
    with pytest.raises(SizeChartValidationError, match="Merchant product ID is required"):
        service.validate_and_normalize_chart(
            merchant_id="m_011",
            merchant_product_id="",
            merchant_name="BrandNoProd",
            basis="BODY",
            unit="CM",
            source_reference="feed",
            source_revision="rev_1",
            rows=[{"merchant_size": "M", "chest": Decimal("100.0")}],
        )


def test_size_013_missing_basis_rejected():
    service = SizeChartService()
    with pytest.raises(SizeChartValidationError, match="Invalid or missing measurement basis"):
        service.validate_and_normalize_chart(
            merchant_id="m_012",
            merchant_product_id="prod_no_basis",
            merchant_name="BrandNoBasis",
            basis="UNKNOWN_BASIS",
            unit="CM",
            source_reference="feed",
            source_revision="rev_1",
            rows=[{"merchant_size": "M", "chest": Decimal("100.0")}],
        )


def test_size_014_unit_conversion_inch_to_cm():
    val_inch = Decimal("40.0")
    cm_result = SizeChartService.convert_to_cm(val_inch, MeasurementUnit.INCH)
    # 40 * 2.54 = 101.60
    assert cm_result == Decimal("101.60")

    val_cm = Decimal("101.60")
    cm_same = SizeChartService.convert_to_cm(val_cm, MeasurementUnit.CM)
    assert cm_same == Decimal("101.60")
