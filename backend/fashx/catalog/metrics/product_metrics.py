from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import (
    CatalogSource,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from database.models.catalog_auth import CatalogSourceStatus
from database.models.catalog_freshness import ProductVariant
from database.models.catalog_sync import CatalogIngestionQuarantine
from fashx.catalog.metrics.contracts import (
    CatalogMetricResult,
    UsableProductCheckResult,
)


async def evaluate_product_usability_metrics(
    session: AsyncSession,
    minimum_usable_offers: int = 1000,
    expansion_minimum_offers: int = 2000,
    expansion_maximum_offers: int = 5000,
) -> tuple[CatalogMetricResult, CatalogMetricResult, UsableProductCheckResult, dict]:
    """Evaluates CAT-TGT-02 (Usable Products) and CAT-TGT-03 (Expansion Range)."""
    now = datetime.now(UTC)

    # 1. Fetch set of quarantined (source_id, source_product_id)
    quarantine_query = select(
        CatalogIngestionQuarantine.source_id,
        CatalogIngestionQuarantine.source_product_id,
    ).where(CatalogIngestionQuarantine.status == "PENDING")
    quarantine_res = await session.execute(quarantine_query)
    quarantined_pairs = {(row[0], row[1]) for row in quarantine_res.all() if row[0] and row[1]}

    # 2. Fetch all merchant offers with joined details
    offers_query = select(MerchantOffer)
    offers_res = await session.execute(offers_query)
    all_offers = list(offers_res.scalars().all())

    # Pre-fetch lookup caches for sources, merchants, garments
    sources_cache: dict[UUID, CatalogSource] = {}
    merchants_cache: dict[UUID, Merchant] = {}
    products_cache: dict[UUID, MerchantProduct] = {}

    usable_offer_ids: list[UUID] = []
    associated_garment_ids: set[UUID] = set()
    seen_source_product_pairs: set[tuple[UUID, str]] = set()

    excluded_duplicates_count = 0
    excluded_quarantined_count = 0
    excluded_inactive_count = 0
    excluded_unauthorized_source_count = 0

    rejection_breakdown: dict[str, int] = {
        "inactive_or_removed": 0,
        "duplicate_pair": 0,
        "quarantined": 0,
        "unauthorized_source": 0,
        "invalid_price": 0,
        "invalid_url": 0,
        "missing_title": 0,
        "unverified_merchant": 0,
    }

    for offer in all_offers:
        # Check active lifecycle
        if offer.status != "ACTIVE":
            excluded_inactive_count += 1
            rejection_breakdown["inactive_or_removed"] += 1
            continue

        # Check duplicate
        pair = (offer.merchant_id, offer.source_product_id)
        if pair in seen_source_product_pairs:
            excluded_duplicates_count += 1
            rejection_breakdown["duplicate_pair"] += 1
            continue
        seen_source_product_pairs.add(pair)

        # Check quarantine
        if offer.source_id and (offer.source_id, offer.source_product_id) in quarantined_pairs:
            excluded_quarantined_count += 1
            rejection_breakdown["quarantined"] += 1
            continue

        # Check source authorization and operational state
        if offer.source_id not in sources_cache:
            src = await session.get(CatalogSource, offer.source_id) if offer.source_id else None
            if src:
                sources_cache[offer.source_id] = src
        source = sources_cache.get(offer.source_id) if offer.source_id else None

        if (
            not source
            or not source.is_enabled
            or source.source_status
            in (
                CatalogSourceStatus.SUSPENDED.value,
                CatalogSourceStatus.REVOKED.value,
                CatalogSourceStatus.EXPIRED.value,
            )
        ):
            excluded_unauthorized_source_count += 1
            rejection_breakdown["unauthorized_source"] += 1
            continue

        # Check merchant verification
        if offer.merchant_id not in merchants_cache:
            m = await session.get(Merchant, offer.merchant_id)
            if m:
                merchants_cache[offer.merchant_id] = m
        merchant = merchants_cache.get(offer.merchant_id)
        if not merchant or merchant.verification_status not in ("VERIFIED", "ACTIVE"):
            rejection_breakdown["unverified_merchant"] += 1
            continue

        # Check price bounds
        if not offer.price_minor or offer.price_minor <= 0:
            rejection_breakdown["invalid_price"] += 1
            continue

        # Check destination URL
        if not offer.url or not (
            offer.url.startswith("http://") or offer.url.startswith("https://")
        ):
            rejection_breakdown["invalid_url"] += 1
            continue

        # Check associated product or garment title
        if offer.merchant_product_id:
            if offer.merchant_product_id not in products_cache:
                p = await session.get(MerchantProduct, offer.merchant_product_id)
                if p:
                    products_cache[offer.merchant_product_id] = p
            prod = products_cache.get(offer.merchant_product_id)
            if prod and (not prod.title or len(prod.title.strip()) < 3):
                rejection_breakdown["missing_title"] += 1
                continue

        # Record as usable offer
        usable_offer_ids.append(offer.id)
        if offer.garment_id:
            associated_garment_ids.add(offer.garment_id)

    usable_offers_count = len(usable_offer_ids)
    canonical_garments_count = len(associated_garment_ids)

    # Count distinct product variants associated with usable offers
    variants_count = 0
    if associated_garment_ids:
        v_query = select(func.count(ProductVariant.id)).where(
            ProductVariant.canonical_garment_id.in_(list(associated_garment_ids))
        )
        variants_count = await session.scalar(v_query) or 0

    breakdown = UsableProductCheckResult(
        usable_offers_count=usable_offers_count,
        canonical_garments_count=canonical_garments_count,
        product_variants_count=variants_count,
        excluded_duplicates_count=excluded_duplicates_count,
        excluded_quarantined_count=excluded_quarantined_count,
        excluded_inactive_count=excluded_inactive_count,
        excluded_unauthorized_source_count=excluded_unauthorized_source_count,
        passed_all=usable_offers_count >= minimum_usable_offers,
    )

    # CAT-TGT-02: Usable products (initial 1,000 target)
    usable_passed = usable_offers_count >= minimum_usable_offers
    usable_result = CatalogMetricResult(
        metric_id="CAT-TGT-02",
        target_value=float(minimum_usable_offers),
        actual_value=float(usable_offers_count),
        unit="usable_offers",
        passed=usable_passed,
        measured_at=now,
        numerator=usable_offers_count,
        denominator=minimum_usable_offers,
        evidence_reference="usable_product_count_snapshot",
        notes=[
            f"Distinct usable merchant offers: {usable_offers_count}/{minimum_usable_offers}.",
            f"Associated distinct canonical garments: {canonical_garments_count}.",
            f"Associated purchasable variants: {variants_count}.",
        ],
    )

    # CAT-TGT-03: Expansion target (2,000–5,000 conditional)
    expansion_eligible = usable_offers_count >= expansion_minimum_offers
    expansion_result = CatalogMetricResult(
        metric_id="CAT-TGT-03",
        target_value=float(expansion_minimum_offers),
        actual_value=float(usable_offers_count),
        unit="usable_offers",
        passed=expansion_eligible,
        measured_at=now,
        numerator=usable_offers_count,
        denominator=expansion_minimum_offers,
        evidence_reference="expansion_readiness_evaluation",
        notes=[
            f"Current offers: {usable_offers_count}. Expansion band: {expansion_minimum_offers}–{expansion_maximum_offers}.",
            "Conditional gate: expansion permitted only after baseline quality gates clear.",
        ],
    )

    details = {
        "rejection_breakdown": rejection_breakdown,
        "usable_offers_count": usable_offers_count,
        "canonical_garments_count": canonical_garments_count,
        "product_variants_count": variants_count,
    }

    return usable_result, expansion_result, breakdown, details
