"""RC12 Catalog Operations and Health Monitor."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class CatalogHealthReport:
    source: str
    last_sync_utc: str
    total_fetched: int
    new_products: int
    updated_products: int
    duplicate_candidates: int
    rejected_by_reason: dict[str, int]
    permission_blocked: int
    stale_prices: int
    stale_availability: int
    published_products: int


def evaluate_catalog_records(
    records: list[dict[str, Any]],
    *,
    source_name: str = "partner_feed_primary",
    max_stale_hours: int = 24,
    reference_time: datetime | None = None,
) -> CatalogHealthReport:
    """Evaluates raw catalog ingestion records and compiles operational health metrics."""
    now = reference_time or datetime.now(UTC)
    total_fetched = len(records)
    new_count = 0
    updated_count = 0
    duplicate_candidates = 0
    rejected_reasons: dict[str, int] = {}
    permission_blocked = 0
    stale_prices = 0
    stale_avail = 0
    published_count = 0

    seen_source_ids: set[str] = set()

    for item in records:
        sid = item.get("source_product_id")
        if sid:
            if sid in seen_source_ids:
                duplicate_candidates += 1
            seen_source_ids.add(sid)

        is_new = item.get("is_new", False)
        if is_new:
            new_count += 1
        else:
            updated_count += 1

        # Permission check
        if not item.get("source_clearance", False):
            permission_blocked += 1
            rejected_reasons["source_not_cleared"] = rejected_reasons.get("source_not_cleared", 0) + 1
            continue

        # Image check
        if not item.get("image_reference"):
            rejected_reasons["missing_image"] = rejected_reasons.get("missing_image", 0) + 1
            continue

        # Price freshness
        price_ts = item.get("price_updated_at")
        if price_ts:
            try:
                dt = datetime.fromisoformat(str(price_ts))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                age_hours = (now - dt).total_seconds() / 3600.0
                if age_hours > max_stale_hours:
                    stale_prices += 1
                    rejected_reasons["stale_price"] = rejected_reasons.get("stale_price", 0) + 1
                    continue
            except Exception:
                rejected_reasons["invalid_price_timestamp"] = rejected_reasons.get("invalid_price_timestamp", 0) + 1
                continue
        else:
            rejected_reasons["missing_price_timestamp"] = rejected_reasons.get("missing_price_timestamp", 0) + 1
            continue

        # In-stock check
        if item.get("in_stock") is False:
            stale_avail += 1

        published_count += 1

    return CatalogHealthReport(
        source=source_name,
        last_sync_utc=now.isoformat(),
        total_fetched=total_fetched,
        new_products=new_count,
        updated_products=updated_count,
        duplicate_candidates=duplicate_candidates,
        rejected_by_reason=rejected_reasons,
        permission_blocked=permission_blocked,
        stale_prices=stale_prices,
        stale_availability=stale_avail,
        published_products=published_count,
    )
