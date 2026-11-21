"""Catalog freshness, lifecycle, and provenance domain models and policies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from database.models.catalog_freshness import (
    AvailabilityStatus,
    CatalogTakedownStatus,
    FreshnessState,
    OfferStatus,
    PriceChangeType,
    ProvenanceEntityType,
    SyncStatus,
)

__all__ = [
    "FreshnessState",
    "OfferStatus",
    "AvailabilityStatus",
    "PriceChangeType",
    "SyncStatus",
    "CatalogTakedownStatus",
    "ProvenanceEntityType",
    "FreshnessPolicy",
    "DEFAULT_FRESHNESS_POLICY",
    "calculate_freshness",
    "AttributeProvenance",
    "PriceObservation",
]


@dataclass(frozen=True)
class FreshnessPolicy:
    """Configurable max-age freshness targets for catalog entities."""

    price_max_age: timedelta = timedelta(hours=6)
    availability_max_age: timedelta = timedelta(hours=2)
    metadata_max_age: timedelta = timedelta(hours=24)
    size_availability_max_age: timedelta = timedelta(hours=2)
    image_reference_max_age: timedelta = timedelta(days=7)
    source_status_max_age: timedelta = timedelta(minutes=15)


DEFAULT_FRESHNESS_POLICY = FreshnessPolicy()


def calculate_freshness(
    last_verified_at: datetime | None,
    max_age: timedelta,
    *,
    now: datetime | None = None,
) -> FreshnessState:
    """Derive freshness state from verification timestamp and max age policy.

    Rules:
    - None timestamp -> UNKNOWN
    - Future timestamp -> REVIEW_REQUIRED
    - Age exceeding max_age -> STALE
    - Otherwise -> CURRENT
    """
    if last_verified_at is None:
        return FreshnessState.UNKNOWN

    current_time = now or datetime.now(UTC)
    if last_verified_at.tzinfo is None:
        # Assume UTC if naive, but enforce comparison
        last_verified_at = last_verified_at.replace(tzinfo=UTC)

    if last_verified_at > current_time:
        return FreshnessState.REVIEW_REQUIRED

    if current_time - last_verified_at > max_age:
        return FreshnessState.STALE

    return FreshnessState.CURRENT


@dataclass
class AttributeProvenance:
    entity_type: ProvenanceEntityType
    entity_id: UUID
    attribute_name: str
    attribute_value: Any
    source_id: UUID
    merchant_id: UUID | None
    ingest_run_id: UUID | None
    confidence: float
    recorded_at: datetime
    source_updated_at: datetime | None = None


@dataclass
class PriceObservation:
    merchant_offer_id: UUID
    merchant_id: UUID
    source_id: UUID
    price_minor: int
    currency: str
    observed_at: datetime
    change_type: PriceChangeType = PriceChangeType.INITIAL
    original_price_minor: int | None = None
    ingest_run_id: UUID | None = None
    source_updated_at: datetime | None = None
