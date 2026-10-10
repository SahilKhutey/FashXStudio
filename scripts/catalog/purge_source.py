"""CLI tool to suspend or delete a catalog source within ≤ 10 minutes (Takedown SLA).

Usage:
    python scripts/catalog/purge_source.py brand-a --mode suspend            # dry-run
    python scripts/catalog/purge_source.py brand-a --mode suspend --apply    # apply suspension
    python scripts/catalog/purge_source.py brand-a --mode delete --apply     # apply full deletion
"""

import argparse
import asyncio
import sys
from datetime import UTC, datetime

from sqlalchemy import delete, select

from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    GarmentEnrichment,
    GarmentImage,
    MerchantOffer,
    MerchantProduct,
)
from fashx.core.database import get_session_factory
from fashx.core.dependencies import get_storage
from fashx.core.settings import get_settings


async def purge_source(args: argparse.Namespace) -> None:
    session_factory = get_session_factory()
    settings = get_settings()

    async with session_factory() as session:
        stmt = select(CatalogSource).where(CatalogSource.slug == args.slug)
        source = (await session.scalars(stmt)).first()
        if source is None:
            print(f"Error: Source '{args.slug}' not found.", file=sys.stderr)
            sys.exit(1)

        # Count affected items
        prod_stmt = select(MerchantProduct).where(MerchantProduct.source_id == source.id)
        products = (await session.scalars(prod_stmt)).all()
        prod_count = len(products)
        source_pids = [p.source_product_id for p in products]

        print(f"Source: {source.slug} ({source.name})")
        print(f"Current Status: {source.status}")
        print(f"Mode: {args.mode.upper()}")
        print(f"Action: {'APPLY CHANGES' if args.apply else 'DRY RUN (no database changes)'}")
        print(f"Found {prod_count} merchant products associated with source '{source.slug}'.")

        if args.mode == "suspend":
            if not args.apply:
                print("\n[DRY RUN] Would update status from '{source.status}' to 'suspended'.")
                print("Run with --apply to execute.")
                return

            source.status = "suspended"
            audit_note = f"[SUSPENDED on {datetime.now(UTC).isoformat()} by operator. Reason: {args.reason}]"
            source.notes = f"{source.notes}\n{audit_note}" if source.notes else audit_note
            await session.commit()
            print(f"\nSUCCESS: Source '{source.slug}' suspended immediately. All items are now excluded from the discovery feed.")
            return

        elif args.mode == "delete":
            # Count offers and garment images
            offer_stmt = select(MerchantOffer).where(MerchantOffer.source_product_id.in_(source_pids))
            offers = (await session.scalars(offer_stmt)).all() if source_pids else []
            offer_count = len(offers)
            garment_ids = list({o.garment_id for o in offers})

            image_count = 0
            enrich_count = 0
            if garment_ids:
                img_stmt = select(GarmentImage).where(GarmentImage.garment_id.in_(garment_ids))
                image_count = len((await session.scalars(img_stmt)).all())

                enr_stmt = select(GarmentEnrichment).where(GarmentEnrichment.garment_id.in_(garment_ids))
                enrich_count = len((await session.scalars(enr_stmt)).all())

            print(f"  - Merchant Offers: {offer_count}")
            print(f"  - Garment Images: {image_count}")
            print(f"  - Enrichments: {enrich_count}")
            prefix = f"catalog/{source.slug}/"
            print(f"  - Object Storage Prefix: {prefix}")

            if not args.apply:
                print(f"\n[DRY RUN] Would delete {prod_count} products, {offer_count} offers, {image_count} images, {enrich_count} enrichments, and purge storage prefix '{prefix}'.")
                print("Run with --apply to execute.")
                return

            # 1. Delete database records
            if garment_ids:
                await session.execute(delete(GarmentEnrichment).where(GarmentEnrichment.garment_id.in_(garment_ids)))
                await session.execute(delete(GarmentImage).where(GarmentImage.garment_id.in_(garment_ids)))
                await session.execute(delete(MerchantOffer).where(MerchantOffer.garment_id.in_(garment_ids)))
                await session.execute(delete(CanonicalGarment).where(CanonicalGarment.id.in_(garment_ids)))

            await session.execute(delete(MerchantProduct).where(MerchantProduct.source_id == source.id))
            source.status = "suspended"
            audit_note = f"[PURGED on {datetime.now(UTC).isoformat()} by operator. Deleted {prod_count} products. Reason: {args.reason}]"
            source.notes = f"{source.notes}\n{audit_note}" if source.notes else audit_note
            await session.commit()

            # 2. Delete storage objects
            deleted_objects = 0
            try:
                storage = get_storage()
                deleted_objects = storage.delete_prefix(prefix)
            except Exception as e:
                print(f"Warning: Storage purge encounter error: {e}", file=sys.stderr)

            print(f"\nSUCCESS: Purged source '{source.slug}'.")
            print(f"  - Removed {prod_count} products, {offer_count} offers, {image_count} images, {enrich_count} enrichments.")
            print(f"  - Purged {deleted_objects} storage objects under '{prefix}'.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Purge or suspend a catalog source (takedown tool).")
    parser.add_argument("slug", help="Slug of the catalog source to purge/suspend")
    parser.add_argument("--mode", choices=["suspend", "delete"], default="suspend", help="Action mode: suspend or delete")
    parser.add_argument("--apply", action="store_true", help="Execute the changes (default is dry-run)")
    parser.add_argument("--reason", default="Partner request / Takedown SLA", help="Audit reason for takedown")

    args = parser.parse_args()
    asyncio.run(purge_source(args))


if __name__ == "__main__":
    main()
