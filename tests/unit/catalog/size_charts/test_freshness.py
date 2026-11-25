"""Tests for Freshness Policy (SZ-FRE-001 - SZ-FRE-004)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fashx.catalog.size_charts.enums import AvailabilityStatus, SizeChartStatus
from fashx.catalog.size_charts.freshness import FreshnessPolicy


def test_chart_freshness_within_90_days():
    """SZ-FRE-001: Size chart active within 90 days is marked fresh."""
    verified_at = datetime.now(UTC) - timedelta(days=30)
    is_stale, status = FreshnessPolicy.evaluate_chart_freshness(
        verified_at, current_status=SizeChartStatus.AVAILABLE
    )
    assert is_stale is False
    assert status == SizeChartStatus.AVAILABLE


def test_chart_freshness_older_than_90_days():
    """SZ-FRE-002: Size chart older than 90 days is marked stale."""
    verified_at = datetime.now(UTC) - timedelta(days=95)
    is_stale, status = FreshnessPolicy.evaluate_chart_freshness(
        verified_at, current_status=SizeChartStatus.AVAILABLE
    )
    assert is_stale is True
    assert status == SizeChartStatus.STALE


def test_inventory_freshness_degrades_to_unknown():
    """SZ-FRE-003: Inventory older than 24 hours degrades from IN_STOCK to UNKNOWN."""
    observed_at = datetime.now(UTC) - timedelta(hours=36)
    is_stale, status = FreshnessPolicy.evaluate_inventory_freshness(
        observed_at, observed_status=AvailabilityStatus.IN_STOCK
    )
    assert is_stale is True
    assert status == AvailabilityStatus.UNKNOWN


def test_inventory_staleness_never_falsifies_out_of_stock():
    """SZ-FRE-004: Inventory staleness never falsifies OUT_OF_STOCK."""
    observed_at = datetime.now(UTC) - timedelta(hours=72)
    is_stale, status = FreshnessPolicy.evaluate_inventory_freshness(
        observed_at, observed_status=AvailabilityStatus.IN_STOCK
    )
    # Stale positive stock becomes UNKNOWN, never OUT_OF_STOCK
    assert status != AvailabilityStatus.OUT_OF_STOCK
    assert status == AvailabilityStatus.UNKNOWN

    # Stale OUT_OF_STOCK remains OUT_OF_STOCK
    is_stale_oos, status_oos = FreshnessPolicy.evaluate_inventory_freshness(
        observed_at, observed_status=AvailabilityStatus.OUT_OF_STOCK
    )
    assert status_oos == AvailabilityStatus.OUT_OF_STOCK
