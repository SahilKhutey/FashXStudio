from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource, MerchantOffer
from fashx.catalog.metrics.contracts import CatalogMetricResult
from fashx.catalog.metrics.sampling import reproducible_sample
from fashx.catalog.metrics.target_config import get_source_freshness_window_hours


async def evaluate_price_freshness(
    session: AsyncSession,
    sample_size: int | None = None,
    random_seed: int = 42,
    minimum_fresh_percentage: float = 95.0,
) -> tuple[CatalogMetricResult, dict]:
    """Evaluates CAT-TGT-04: At least 95% price freshness within per-source freshness windows."""
    now = datetime.now(UTC)

    # 1. Fetch all eligible active offers
    query = select(MerchantOffer).where(
        MerchantOffer.status == "ACTIVE",
        MerchantOffer.in_stock == True,  # noqa: E712
    )
    result = await session.execute(query)
    eligible_offers = list(result.scalars().all())

    if not eligible_offers:
        empty_res = CatalogMetricResult(
            metric_id="CAT-TGT-04",
            target_value=minimum_fresh_percentage,
            actual_value=0.0,
            unit="percent",
            passed=False,
            measured_at=now,
            numerator=0,
            denominator=0,
            sample_size=0,
            evidence_reference="price_freshness_audit",
            notes=["No active in-stock offers found in catalog for price freshness evaluation."],
        )
        return empty_res, {"fresh_count": 0, "stale_count": 0, "unverified_count": 0}

    # 2. Sample offers if sample_size is requested
    sampled_offers = (
        reproducible_sample(eligible_offers, sample_size, random_seed=random_seed)
        if sample_size and sample_size < len(eligible_offers)
        else eligible_offers
    )

    # 3. Source freshness window cache
    sources_cache: dict[UUID, int] = {}

    fresh_count = 0
    stale_count = 0
    unverified_count = 0
    currencies_observed: set[str] = set()
    unverified_offer_ids: list[str] = []

    for offer in sampled_offers:
        currencies_observed.add(offer.currency)

        # Retrieve per-source agreed freshness window
        if offer.source_id and offer.source_id not in sources_cache:
            src = await session.get(CatalogSource, offer.source_id)
            sources_cache[offer.source_id] = get_source_freshness_window_hours(src)
        window_hours = sources_cache.get(offer.source_id, 24)
        freshness_cutoff = now - timedelta(hours=window_hours)

        last_verified = offer.last_price_verified_at
        if last_verified is not None and last_verified.tzinfo is None:
            last_verified = last_verified.replace(tzinfo=UTC)

        if last_verified is None:
            unverified_count += 1
            unverified_offer_ids.append(str(offer.id))
        elif last_verified >= freshness_cutoff:
            fresh_count += 1
        else:
            stale_count += 1

    total_sampled = len(sampled_offers)
    actual_percentage = (
        round((fresh_count / total_sampled) * 100.0, 2) if total_sampled > 0 else 0.0
    )
    passed = actual_percentage >= minimum_fresh_percentage

    metric_result = CatalogMetricResult(
        metric_id="CAT-TGT-04",
        target_value=minimum_fresh_percentage,
        actual_value=actual_percentage,
        unit="percent",
        passed=passed,
        measured_at=now,
        numerator=fresh_count,
        denominator=total_sampled,
        sample_size=total_sampled,
        evidence_reference="price_freshness_audit",
        notes=[
            f"Price freshness: {actual_percentage}% (threshold: >={minimum_fresh_percentage}%).",
            f"Counts: fresh={fresh_count}, stale={stale_count}, unverified={unverified_count}.",
            f"Currencies observed: {sorted(currencies_observed)}.",
        ],
    )

    details = {
        "total_eligible_offers": len(eligible_offers),
        "total_sampled": total_sampled,
        "fresh_count": fresh_count,
        "stale_count": stale_count,
        "unverified_count": unverified_count,
        "unverified_offer_ids": unverified_offer_ids[:50],
        "currencies": sorted(currencies_observed),
        "currencies_observed": sorted(currencies_observed),
    }

    return metric_result, details
