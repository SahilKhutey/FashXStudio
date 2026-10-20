#!/usr/bin/env python3
"""Seed local own-wardrobe garments from a CSV file and image directory.

Bypasses external HTTPS download and mock VLM enrichment by applying human-labeled
attributes with 1.0 confidence, computing try-on eligibility through the canonical gate,
and storing images in local/mirror storage.

Usage:
    python scripts/catalog/seed_local.py --csv catalog_seed/catalog.csv --dry-run
    python scripts/catalog/seed_local.py --csv catalog_seed/catalog.csv --apply
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import (
    Brand,
    CanonicalGarment,
    CatalogSource,
    GarmentEnrichment,
    GarmentImage,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from fashx.catalog.eligibility import compute_tryon_eligibility
from fashx.core.database import get_session_factory
from fashx.core.dependencies import get_storage


def parse_sizes(sizes_str: str) -> list[str]:
    if not sizes_str:
        return []
    parts = sizes_str.replace(",", "|").split("|")
    return [p.strip().upper() for p in parts if p.strip()]


async def seed_local_catalog(
    csv_path: Path,
    apply: bool,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    storage: Any | None = None,
) -> None:
    if not csv_path.exists():
        print(f"Error: CSV file '{csv_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    csv_dir = csv_path.parent
    if session_factory is None:
        session_factory = get_session_factory()
    if storage is None:
        storage = get_storage()

    async with session_factory() as session:
        # 1. Verify cleared own-wardrobe source
        stmt = select(CatalogSource).where(CatalogSource.slug == "own-wardrobe")
        source = (await session.scalars(stmt)).first()
        if source is None:
            print(
                "Error: Source 'own-wardrobe' not registered. Run:\n"
                "  python scripts/catalog/register_source.py --slug own-wardrobe --name 'Own wardrobe' --kind manual --image-policy mirror\n"
                "  python scripts/catalog/clear_source.py own-wardrobe --evidence-url 'docs/evidence/own-wardrobe-consent.md' --display --tryon",
                file=sys.stderr,
            )
            sys.exit(1)

        if source.status != "cleared":
            print(
                f"Error: Source 'own-wardrobe' has status '{source.status}', must be 'cleared'. Run clear_source.py.",
                file=sys.stderr,
            )
            sys.exit(1)

        # 2. Get or create Merchant & Brand
        m_stmt = select(Merchant).where(Merchant.name == "Own Wardrobe")
        merchant = (await session.scalars(m_stmt)).first()
        if merchant is None and apply:
            merchant = Merchant(name="Own Wardrobe", merchant_type="manual")
            session.add(merchant)
            await session.flush()
        elif merchant is None:
            merchant = Merchant(id=uuid4(), name="Own Wardrobe", merchant_type="manual")

        b_stmt = select(Brand).where(Brand.name == "Own")
        brand = (await session.scalars(b_stmt)).first()
        if brand is None and apply:
            brand = Brand(name="Own", normalized_name="own")
            session.add(brand)
            await session.flush()
        elif brand is None:
            brand = Brand(id=uuid4(), name="Own", normalized_name="own")

        # 3. Read and validate CSV rows
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"Found {len(rows)} garment entries in '{csv_path}'.")
        print(f"Mode: {'APPLY (writing to database & storage)' if apply else 'DRY-RUN (no changes written)'}\n")

        processed = 0
        eligible_count = 0

        for r in rows:
            g_id = r["id"].strip()
            title = r["title"].strip()
            category = r.get("category", "tops").strip().lower()
            sub_category = r.get("sub_category", "").strip().lower() or None
            gender = r.get("gender", "unisex").strip().lower()
            try:
                price_val = float(r.get("price", "0").strip())
                price_minor = int(price_val * 100)
            except ValueError:
                price_minor = 0

            sizes = parse_sizes(r.get("sizes", ""))
            tryon_suitable_bool = r.get("tryon_suitable", "true").strip().lower() in ("true", "1", "yes")

            # Check image file
            img_rel_path = r.get("image", "").strip()
            img_path = csv_dir / img_rel_path
            if not img_path.exists():
                img_path = Path(img_rel_path)

            if img_path.exists():
                img_bytes = img_path.read_bytes()
                content_hash = hashlib.sha256(img_bytes).hexdigest()
            else:
                img_bytes = b""
                content_hash = hashlib.sha256(g_id.encode()).hexdigest()

            storage_key = f"catalog/own-wardrobe/{content_hash}.jpg"

            # Compute tryon eligibility
            is_eligible = compute_tryon_eligibility(
                source_rights_tryon=source.rights_tryon,
                source_image_policy=source.image_policy,
                vlm_tryon_suitable=tryon_suitable_bool,
                vlm_confidence=1.0,
                category=category,
            )
            if is_eligible:
                eligible_count += 1

            if not apply:
                print(
                    f"  [DRY-RUN] {g_id}: '{title}' | Category: {category} | Sizes: {sizes} | "
                    f"Price: INR {price_minor/100:.2f} | Try-on eligible: {is_eligible} | Image: {img_path if img_path.exists() else 'NOT FOUND'}"
                )
                processed += 1
                continue

            # APPLY MODE:
            now = datetime.now(UTC)

            # Put image into storage
            if img_bytes:
                storage.put(storage_key, img_bytes, "image/jpeg")

            # Ingest/Upsert MerchantProduct
            mp_stmt = select(MerchantProduct).where(
                MerchantProduct.merchant_id == merchant.id,
                MerchantProduct.source_product_id == g_id,
            )
            product = (await session.scalars(mp_stmt)).first()
            if product is None:
                product = MerchantProduct(
                    merchant_id=merchant.id,
                    brand_id=brand.id,
                    source_id=source.id,
                    source_product_id=g_id,
                    title=title,
                    description=title,
                    source_url=f"own-wardrobe://{g_id}",
                    status="active",
                    content_hash=content_hash,
                    last_seen_at=now,
                    price_checked_at=now,
                )
                session.add(product)
                await session.flush()
            else:
                product.title = title
                product.content_hash = content_hash
                product.last_seen_at = now
                product.price_checked_at = now
                product.status = "active"
                await session.flush()

            # Find or create CanonicalGarment
            cg_stmt = select(CanonicalGarment).where(
                CanonicalGarment.brand_id == brand.id,
                CanonicalGarment.display_name == title,
            )
            garment = (await session.scalars(cg_stmt)).first()
            if garment is None:
                garment = CanonicalGarment(
                    brand_id=brand.id,
                    display_name=title,
                    category=category,
                    subcategory=sub_category,
                    gender=gender,
                    price_minor=price_minor,
                    sizes_in_stock=sizes,
                    tryon_supported=is_eligible,
                    price_updated_at=now,
                    version=1,
                )
                session.add(garment)
                await session.flush()
            else:
                garment.category = category
                garment.subcategory = sub_category
                garment.price_minor = price_minor
                garment.sizes_in_stock = sizes
                garment.tryon_supported = is_eligible
                garment.price_updated_at = now
                await session.flush()

            # Link MerchantOffer
            offer_stmt = select(MerchantOffer).where(
                MerchantOffer.merchant_id == merchant.id,
                MerchantOffer.source_product_id == g_id,
            )
            offer = (await session.scalars(offer_stmt)).first()
            if offer is None:
                offer = MerchantOffer(
                    garment_id=garment.id,
                    merchant_id=merchant.id,
                    source_product_id=g_id,
                    url=f"own-wardrobe://{g_id}",
                    price_minor=price_minor,
                    currency="INR",
                    in_stock=True,
                    last_synced_at=now,
                )
                session.add(offer)
                await session.flush()
            else:
                offer.price_minor = price_minor
                offer.in_stock = True
                offer.last_synced_at = now
                await session.flush()

            # Link GarmentImage
            img_stmt = select(GarmentImage).where(
                GarmentImage.garment_id == garment.id,
                GarmentImage.content_hash == content_hash,
            )
            g_img = (await session.scalars(img_stmt)).first()
            if g_img is None:
                g_img = GarmentImage(
                    garment_id=garment.id,
                    storage_key=storage_key,
                    content_hash=content_hash,
                    image_type="primary",
                    version=1,
                )
                session.add(g_img)
                await session.flush()

            # Attach Human-Enriched Attributes
            human_attrs = {
                "category": category,
                "subcategory": sub_category or "",
                "primary_color": r.get("primary_color", "").strip(),
                "pattern": r.get("pattern", "solid").strip(),
                "formality": int(r.get("formality", "3").strip() or 3),
                "ethnic_wear": r.get("ethnic_wear", "false").strip().lower() in ("true", "1", "yes"),
                "tryon_suitable": tryon_suitable_bool,
                "source_of_truth": "human",
            }
            enrichment_stmt = select(GarmentEnrichment).where(
                GarmentEnrichment.garment_id == garment.id
            )
            enrichment = (await session.scalars(enrichment_stmt)).first()
            if enrichment is None:
                enrichment = GarmentEnrichment(
                    garment_id=garment.id,
                    image_id=g_img.id,
                    model_version="human-expert-1.0",
                    attributes_json=human_attrs,
                    embedding=[0.05] * 512,  # Baseline 512-dim embedding
                    confidence_summary={"overall": 1.0, "source": "human"},
                )
                session.add(enrichment)
            else:
                enrichment.attributes_json = human_attrs
                enrichment.confidence_summary = {"overall": 1.0, "source": "human"}

            await session.flush()
            print(f"  [APPLY] Ingested '{title}' (ID: {garment.id}) | Try-on eligible: {is_eligible}")
            processed += 1

        if apply:
            await session.commit()
            print(f"\nSuccessfully seeded {processed} garments ({eligible_count} try-on eligible) to catalog.")
        else:
            print(f"\nDry-run complete for {processed} garments ({eligible_count} try-on eligible).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed local catalog garments from CSV")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("catalog_seed/catalog.csv"),
        help="Path to catalog CSV (default: catalog_seed/catalog.csv)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True, help="Simulate run without writing changes (default)")
    group.add_argument("--apply", action="store_true", help="Apply changes to database and storage")

    args = parser.parse_args()
    apply_mode = bool(args.apply)
    asyncio.run(seed_local_catalog(args.csv, apply=apply_mode))


if __name__ == "__main__":
    main()
