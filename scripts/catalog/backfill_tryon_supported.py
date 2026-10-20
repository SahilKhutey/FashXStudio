"""CLI tool to backfill tryon_supported on canonical garments.

Evaluates try-on eligibility using compute_tryon_eligibility (the single source of truth),
requiring all 4 conditions:
  1. Source rights_tryon is True (and source is 'cleared')
  2. Source image_policy == 'mirror'
  3. VLM enrichment tryon_suitable is True at calibrated confidence (>= tau)
  4. Garment category is in supported categories (tops, bottoms, one-pieces, etc.)

Dry-run is the default. To apply changes to the database, use --apply.

Usage:
    python scripts/catalog/backfill_tryon_supported.py           # dry-run simulation
    python scripts/catalog/backfill_tryon_supported.py --apply   # write updates to DB
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    GarmentEnrichment,
    MerchantOffer,
    MerchantProduct,
)
from fashx.catalog.eligibility import compute_tryon_eligibility
from fashx.core.database import get_session_factory


def evaluate_garment_tryon_eligibility(
    *,
    category: str,
    source_rights_tryon: bool,
    source_image_policy: str,
    source_status: str = "cleared",
    vlm_tryon_suitable: bool = True,
    vlm_confidence: float = 1.0,
    tau: float = 0.85,
) -> bool:
    """Evaluate try-on eligibility using the single source of truth compute_tryon_eligibility."""
    if source_status != "cleared":
        return False
    return compute_tryon_eligibility(
        source_rights_tryon=source_rights_tryon,
        source_image_policy=source_image_policy,
        vlm_tryon_suitable=vlm_tryon_suitable,
        vlm_confidence=vlm_confidence,
        category=category,
        tau=tau,
    )


async def backfill_tryon_supported(
    session: AsyncSession,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Scans all canonical garments, evaluates multi-factor eligibility, and optionally applies updates."""
    # 1. Fetch all canonical garments
    garments = (await session.scalars(select(CanonicalGarment))).all()

    total_scanned = len(garments)
    eligible_count = 0
    updated_count = 0

    for garment in garments:
        # A. Find associated source through offers -> products -> catalog_sources
        source_stmt = (
            select(CatalogSource)
            .join(MerchantProduct, MerchantProduct.source_id == CatalogSource.id)
            .join(
                MerchantOffer,
                (MerchantOffer.merchant_id == MerchantProduct.merchant_id)
                & (MerchantOffer.source_product_id == MerchantProduct.source_product_id),
            )
            .where(MerchantOffer.garment_id == garment.id)
        )
        sources = (await session.scalars(source_stmt)).all()

        # Pick best source (cleared + mirror + rights preferred)
        best_source: CatalogSource | None = None
        for s in sources:
            if s.status == "cleared" and s.rights_tryon and s.image_policy == "mirror":
                best_source = s
                break
        if best_source is None and sources:
            best_source = sources[0]

        source_rights = best_source.rights_tryon if best_source else False
        source_policy = best_source.image_policy if best_source else "hotlink"
        source_status = best_source.status if best_source else "pending"

        # B. Find latest enrichment for garment
        enrichment_stmt = (
            select(GarmentEnrichment)
            .where(GarmentEnrichment.garment_id == garment.id)
            .order_by(GarmentEnrichment.created_at.desc())
        )
        enrichment = (await session.scalars(enrichment_stmt)).first()

        if enrichment is not None:
            attrs = enrichment.attributes_json or {}
            vlm_tryon_suitable = bool(attrs.get("tryon_suitable", False))
            conf_dict = enrichment.confidence_summary or {}
            if "tryon_suitable" in conf_dict:
                vlm_conf = float(conf_dict["tryon_suitable"])
            elif "category" in conf_dict:
                vlm_conf = float(conf_dict["category"])
            elif "confidence" in attrs and isinstance(attrs["confidence"], dict):
                vlm_conf = float(attrs["confidence"].get("category", 1.0))
            else:
                vlm_conf = 1.0
        else:
            vlm_tryon_suitable = False
            vlm_conf = 0.0

        is_eligible = evaluate_garment_tryon_eligibility(
            category=garment.category,
            source_rights_tryon=source_rights,
            source_image_policy=source_policy,
            source_status=source_status,
            vlm_tryon_suitable=vlm_tryon_suitable,
            vlm_confidence=vlm_conf,
        )

        if is_eligible:
            eligible_count += 1

        if garment.tryon_supported != is_eligible:
            updated_count += 1
            if not dry_run:
                garment.tryon_supported = is_eligible

    if not dry_run:
        await session.commit()

    return {
        "total_scanned": total_scanned,
        "eligible": eligible_count,
        "updated": updated_count,
        "dry_run": dry_run,
    }


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill tryon_supported on canonical garments using compute_tryon_eligibility."
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=True,
        help="Simulate backfill without committing changes (default: True)",
    )
    parser.add_argument(
        "--apply",
        dest="dry_run",
        action="store_false",
        help="Apply and commit changes to the database",
    )
    return parser.parse_args(args)


async def main() -> None:
    args = parse_args(sys.argv[1:])
    session_factory = get_session_factory()
    async with session_factory() as session:
        stats = await backfill_tryon_supported(session, dry_run=args.dry_run)
        mode_str = "[DRY-RUN]" if stats["dry_run"] else "[APPLIED]"
        action_verb = "would be updated" if stats["dry_run"] else "updated in database"
        print(f"{mode_str} Scanned: {stats['total_scanned']}, Eligible: {stats['eligible']}, {stats['updated']} {action_verb}.")


if __name__ == "__main__":
    asyncio.run(main())
