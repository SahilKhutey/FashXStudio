"""Freshness evaluation and expiration policies for Phase 08.1."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from .enums import AvailabilityStatus, SizeChartStatus


class FreshnessPolicy:
    """Manages staleness evaluation for merchant size charts and product variant availability."""

    DEFAULT_CHART_FRESHNESS_DAYS = 90
    DEFAULT_INVENTORY_FRESHNESS_HOURS = 24

    @classmethod
    def is_chart_fresh(
        cls,
        last_verified_at: datetime | None,
        max_age_days: int | None = None,
    ) -> bool:
        """Return True if the chart was verified within the allowed freshness window."""
        if last_verified_at is None:
            return False

        allowed_days = max_age_days or cls.DEFAULT_CHART_FRESHNESS_DAYS
        cutoff = datetime.now(UTC) - timedelta(days=allowed_days)

        if last_verified_at.tzinfo is None:
            ts = last_verified_at.replace(tzinfo=UTC)
        else:
            ts = last_verified_at

        return ts >= cutoff

    @classmethod
    def evaluate_chart_freshness(
        cls,
        last_verified_at: datetime | None,
        current_status: SizeChartStatus = SizeChartStatus.AVAILABLE,
        max_age_days: int | None = None,
    ) -> tuple[bool, SizeChartStatus]:
        """Return (is_stale, effective_status) for a size chart."""
        is_fresh = cls.is_chart_fresh(last_verified_at, max_age_days)
        is_stale = not is_fresh
        status = SizeChartStatus.STALE if is_stale else current_status
        return is_stale, status

    @classmethod
    def evaluate_inventory_freshness(
        cls,
        last_seen_at: datetime | None,
        current_status: AvailabilityStatus | None = None,
        *,
        observed_status: AvailabilityStatus | None = None,
        max_age_hours: int | None = None,
    ) -> tuple[bool, AvailabilityStatus]:
        """Return (is_stale, effective_status) for an inventory observation.

        Invariant: Expired inventory observations must transition to UNKNOWN, NEVER to OUT_OF_STOCK.
        """
        stat = observed_status or current_status or AvailabilityStatus.UNKNOWN

        # Takedown, delisted, and discontinued are permanent until explicitly changed
        if stat in (
            AvailabilityStatus.TAKEDOWN,
            AvailabilityStatus.DELISTED,
            AvailabilityStatus.DISCONTINUED,
        ):
            return False, stat

        if last_seen_at is None:
            return True, AvailabilityStatus.UNKNOWN

        allowed_hours = max_age_hours or cls.DEFAULT_INVENTORY_FRESHNESS_HOURS
        cutoff = datetime.now(UTC) - timedelta(hours=allowed_hours)

        if last_seen_at.tzinfo is None:
            ts = last_seen_at.replace(tzinfo=UTC)
        else:
            ts = last_seen_at

        if ts < cutoff:
            # Stale inventory transitions to UNKNOWN unless it was definitively OUT_OF_STOCK
            if stat == AvailabilityStatus.OUT_OF_STOCK:
                return True, AvailabilityStatus.OUT_OF_STOCK
            return True, AvailabilityStatus.UNKNOWN

        return False, stat
