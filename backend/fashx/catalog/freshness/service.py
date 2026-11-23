"""Catalog freshness evaluation and verification service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import MerchantOffer
from database.models.catalog_freshness import (
    FreshnessState,
    OfferPriceHistory,
    PriceChangeType,
    SyncStatus,
)
from fashx.catalog.freshness.models import (
    DEFAULT_FRESHNESS_POLICY,
    FreshnessPolicy,
    calculate_freshness,
)


class CatalogFreshnessService:
    """Manages offer freshness assessment, verification timestamps, and price history."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def evaluate_offer_freshness(
        self,
        offer: MerchantOffer,
        policy: FreshnessPolicy = DEFAULT_FRESHNESS_POLICY,
        now: datetime | None = None,
    ) -> dict[str, FreshnessState]:
        """Assess field-level and aggregate freshness for a merchant offer."""
        current_time = now or datetime.now(UTC)

        price_freshness = calculate_freshness(
            offer.last_price_verified_at or offer.last_verified_at,
            policy.price_max_age,
            now=current_time,
        )
        avail_freshness = calculate_freshness(
            offer.last_availability_verified_at or offer.last_verified_at,
            policy.availability_max_age,
            now=current_time,
        )

        # Aggregate: if either critical dimension is STALE, overall is STALE
        if (
            price_freshness == FreshnessState.REVIEW_REQUIRED
            or avail_freshness == FreshnessState.REVIEW_REQUIRED
        ):
            overall = FreshnessState.REVIEW_REQUIRED
        elif price_freshness == FreshnessState.STALE or avail_freshness == FreshnessState.STALE:
            overall = FreshnessState.STALE
        elif price_freshness == FreshnessState.UNKNOWN or avail_freshness == FreshnessState.UNKNOWN:
            overall = FreshnessState.UNKNOWN
        else:
            overall = FreshnessState.CURRENT

        return {
            "price": price_freshness,
            "availability": avail_freshness,
            "overall": overall,
        }

    async def record_price_observation(
        self,
        offer: MerchantOffer,
        observed_price_minor: int,
        currency: str,
        source_id: UUID,
        merchant_id: UUID,
        ingest_run_id: UUID | None = None,
        original_price_minor: int | None = None,
        source_updated_at: datetime | None = None,
        observed_at: datetime | None = None,
    ) -> OfferPriceHistory | None:
        """Insert a price history record ONLY if price or currency has changed.

        Preserves Section 5.5.6 invariant:
        - Insert a new observation when the effective price changes.
        - Do not insert a duplicate observation for every unchanged feed refresh.
        """
        obs_time = observed_at or datetime.now(UTC)

        # Check existing price
        price_changed = offer.price_minor != observed_price_minor or offer.currency != currency

        # Update offer timestamps
        offer.last_price_verified_at = obs_time
        offer.last_verified_at = obs_time
        offer.last_seen_at = obs_time

        if not price_changed and offer.last_changed_at is not None:
            # Price unchanged; update verified timestamp only
            return None

        # Determine price change type
        if offer.last_changed_at is None:
            change_type = PriceChangeType.INITIAL
        elif offer.currency != currency:
            change_type = PriceChangeType.CURRENCY_CHANGE
        elif observed_price_minor < offer.price_minor:
            change_type = PriceChangeType.PRICE_DROP
        elif observed_price_minor > offer.price_minor:
            change_type = PriceChangeType.PRICE_INCREASE
        else:
            change_type = PriceChangeType.INITIAL

        # Update offer
        offer.price_minor = observed_price_minor
        offer.currency = currency
        if original_price_minor is not None:
            offer.original_price_minor = original_price_minor
            if original_price_minor > observed_price_minor:
                offer.discount_percentage = round(
                    ((original_price_minor - observed_price_minor) / original_price_minor) * 100,
                    2,
                )
        offer.last_changed_at = obs_time
        offer.source_updated_at = source_updated_at
        offer.sync_status = SyncStatus.CURRENT

        # Insert history record
        history_entry = OfferPriceHistory(
            merchant_offer_id=offer.id,
            merchant_id=merchant_id,
            source_id=source_id,
            ingest_run_id=ingest_run_id,
            price_minor=observed_price_minor,
            original_price_minor=original_price_minor,
            currency=currency,
            change_type=change_type,
            observed_at=obs_time,
            source_updated_at=source_updated_at,
            recorded_at=obs_time,
        )
        self.session.add(history_entry)
        return history_entry

    async def record_availability_observation(
        self,
        offer: MerchantOffer,
        in_stock: bool,
        availability: str = "IN_STOCK",
        observed_at: datetime | None = None,
    ) -> bool:
        """Update availability verification timestamps and stock status."""
        obs_time = observed_at or datetime.now(UTC)
        stock_changed = offer.in_stock != in_stock or offer.availability != availability

        offer.in_stock = in_stock
        offer.availability = availability
        offer.last_availability_verified_at = obs_time
        offer.last_verified_at = obs_time
        offer.last_seen_at = obs_time

        if stock_changed:
            offer.last_changed_at = obs_time

        return stock_changed

    async def list_stale_offers(
        self,
        max_age_hours: int = 6,
        merchant_id: UUID | None = None,
        limit: int = 100,
    ) -> list[MerchantOffer]:
        """Find active offers that have exceeded freshness threshold."""
        from datetime import timedelta

        threshold = datetime.now(UTC) - timedelta(hours=max_age_hours)

        stmt = select(MerchantOffer).where(
            MerchantOffer.status == "ACTIVE",
            (MerchantOffer.last_verified_at < threshold)
            | (MerchantOffer.last_verified_at.is_(None)),
        )
        if merchant_id:
            stmt = stmt.where(MerchantOffer.merchant_id == merchant_id)

        stmt = stmt.order_by(MerchantOffer.last_verified_at.asc().nullsfirst()).limit(limit)
        result = await self.session.scalars(stmt)
        return list(result.all())
