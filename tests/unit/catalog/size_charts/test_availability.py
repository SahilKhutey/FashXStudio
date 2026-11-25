"""Tests for Variant Availability (SZ-AVL-001)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fashx.catalog.size_charts.availability import VariantAvailabilityService
from fashx.catalog.size_charts.enums import AvailabilityStatus


def test_variant_availability_aggregation():
    """SZ-AVL-001: Ingest inventory snapshots and report current variant stock."""
    service = VariantAvailabilityService()
    p_id = uuid4()
    now = datetime.now(UTC)

    # Ingest 3 variants
    service.ingest_inventory_snapshot(
        merchant_product_id=p_id,
        variant_id="var_s",
        size_label="S",
        status=AvailabilityStatus.IN_STOCK,
        observed_at=now,
    )
    service.ingest_inventory_snapshot(
        merchant_product_id=p_id,
        variant_id="var_m",
        size_label="M",
        status=AvailabilityStatus.OUT_OF_STOCK,
        observed_at=now,
    )
    service.ingest_inventory_snapshot(
        merchant_product_id=p_id,
        variant_id="var_l",
        size_label="L",
        status=AvailabilityStatus.LOW_STOCK,
        observed_at=now,
    )

    result = service.get_product_availability(p_id)
    assert result.merchant_product_id == p_id
    assert len(result.variants) == 3
    assert result.overall_status == AvailabilityStatus.IN_STOCK

    # Check individual variants
    s_var = service.get_variant_availability(p_id, "var_s")
    assert s_var is not None
    assert s_var.status == AvailabilityStatus.IN_STOCK

    m_var = service.get_variant_availability(p_id, "var_m")
    assert m_var is not None
    assert m_var.status == AvailabilityStatus.OUT_OF_STOCK


def test_all_out_of_stock_product_status():
    """When all variants are out of stock, overall product status is OUT_OF_STOCK."""
    service = VariantAvailabilityService()
    p_id = uuid4()
    now = datetime.now(UTC)

    service.ingest_inventory_snapshot(
        merchant_product_id=p_id,
        variant_id="var_1",
        size_label="M",
        status=AvailabilityStatus.OUT_OF_STOCK,
        observed_at=now,
    )
    result = service.get_product_availability(p_id)
    assert result.overall_status == AvailabilityStatus.OUT_OF_STOCK
