"""Catalog ingestion pipeline orchestrator with safety guards, idempotency, and run reporting."""

import hashlib
from collections import defaultdict
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    CategoryMap,
    GarmentImage,
    IngestRun,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from fashx.application.ports.storage import ObjectStorage

from .dedup import evaluate_dedup
from .google_feed import map_row, rows_from_csv, rows_from_xml
from .image_pipeline import ImageRef, process_image
from .model import CanonicalProduct
from .normalizer import normalize_color, normalize_size, validate_age_group
from .safe_http import RateLimiter, Reject


def compute_content_hash(p: CanonicalProduct) -> str:
    """Compute deterministic SHA-256 hash over core product fields."""
    raw = (
        f"{p.title}|{p.description}|{p.price}|{p.sale_price}|"
        f"{p.in_stock}|{p.image_url}|{p.size}|{p.color}|{p.link}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class IngestPipeline:
    """End-to-end ingestion pipeline executing safe fetch, mapping, normalization, image processing, and idempotent storage."""

    def __init__(
        self,
        session: AsyncSession,
        storage: ObjectStorage | None = None,
        http_client: httpx.Client | None = None,
    ):
        self.session = session
        self.storage = storage
        self.client = http_client or httpx.Client(timeout=30.0)

    async def run(
        self,
        *,
        source_slug: str,
        feed_data: bytes | None = None,
        feed_format: str = "csv",
        limit: int | None = None,
        dry_run: bool = False,
    ) -> IngestRun:
        # 1. Fetch Source
        stmt = select(CatalogSource).where(CatalogSource.slug == source_slug)
        source = (await self.session.scalars(stmt)).first()
        if source is None:
            raise ValueError(f"Source '{source_slug}' not found.")

        if source.status != "cleared" and not dry_run:
            raise ValueError(
                f"Source '{source_slug}' is not cleared (status='{source.status}'). "
                "Only cleared sources may be ingested into production. Use --dry-run to test."
            )

        # 2. Get or create Merchant entity representing this source
        merchant_stmt = select(Merchant).where(Merchant.name == source.name)
        merchant = (await self.session.scalars(merchant_stmt)).first()
        if merchant is None:
            merchant = Merchant(name=source.name, merchant_type=source.kind)
            self.session.add(merchant)
            await self.session.flush()

        # 3. Create IngestRun tracking row
        now = datetime.now(UTC)
        run = IngestRun(
            source_id=source.id,
            started_at=now,
            status="running",
            counts={},
        )
        self.session.add(run)
        await self.session.flush()

        counts: dict[str, Any] = {
            "fetched": 0,
            "new": 0,
            "updated": 0,
            "unchanged": 0,
            "rejected": defaultdict(int),
            "images_ok": 0,
            "images_failed": 0,
            "deduped": 0,
            "blocked_unmapped_category": 0,
            "stale_marked": 0,
            "removed": 0,
        }

        # 4. Stream raw rows
        rows: Iterator[dict[str, str]]
        if feed_data:
            if feed_format == "xml":
                rows = rows_from_xml(feed_data)
            else:
                rows = rows_from_csv(feed_data)
        else:
            rows = iter([])

        # Preload category mapping for this source
        cat_map_stmt = select(CategoryMap).where(CategoryMap.source_id == source.id)
        cat_mappings = {m.source_category: m.taxonomy_id for m in (await self.session.scalars(cat_map_stmt)).all()}

        # Preload existing products for this source
        prod_stmt = select(MerchantProduct).where(MerchantProduct.source_id == source.id)
        existing_products = {p.source_product_id: p for p in (await self.session.scalars(prod_stmt)).all()}
        previous_count = len(existing_products)

        limiter = RateLimiter(float(source.max_rps))
        seen_source_ids: set[str] = set()

        # Track existing items for dedup comparisons
        dedup_records: list[dict] = [
            {
                "source_product_id": p.source_product_id,
                "item_group_id": p.item_group_id,
                "image_sha256": None,
                "image_dhash": None,
                "brand": None,
                "category": None,
                "canonical_garment_id": str(p.id),
            }
            for p in existing_products.values()
        ]

        try:
            for raw_row in rows:
                if limit and counts["fetched"] >= limit:
                    break
                counts["fetched"] += 1

                # Step A: Map to CanonicalProduct
                try:
                    product = map_row(raw_row)
                    validate_age_group(product.age_group)
                except Reject as e:
                    counts["rejected"][e.code] += 1
                    continue
                except Exception as e:
                    counts["rejected"][f"parse_error_{type(e).__name__}"] += 1
                    continue

                seen_source_ids.add(product.source_product_id)

                # Step B: Normalization
                _, canonical_color = normalize_color(product.color)
                _, canonical_size = normalize_size(product.size)

                # Step C: Category mapping check
                taxonomy_category = None
                product_status = "active"
                if product.source_category:
                    if product.source_category in cat_mappings:
                        taxonomy_category = cat_mappings[product.source_category]
                        if not taxonomy_category:
                            product_status = "blocked"
                            counts["blocked_unmapped_category"] += 1
                    else:
                        # Auto-record unmapped category with NULL taxonomy_id
                        cat_entry = CategoryMap(
                            source_id=source.id,
                            source_category=product.source_category,
                            taxonomy_id=None,
                        )
                        self.session.add(cat_entry)
                        cat_mappings[product.source_category] = None
                        product_status = "blocked"
                        counts["blocked_unmapped_category"] += 1

                content_hash = compute_content_hash(product)

                # Step D: Change check
                existing = existing_products.get(product.source_product_id)
                if existing:
                    if existing.content_hash == content_hash:
                        # Unchanged
                        counts["unchanged"] += 1
                        if not dry_run:
                            existing.last_seen_at = now
                        continue
                    else:
                        # Changed
                        counts["updated"] += 1
                        if not dry_run:
                            existing.title = product.title
                            existing.description = product.description
                            existing.source_url = str(product.link)
                            existing.content_hash = content_hash
                            existing.last_seen_at = now
                            existing.price_checked_at = now
                            existing.status = product_status

                            # Update offer
                            offer_stmt = select(MerchantOffer).where(
                                MerchantOffer.merchant_id == merchant.id,
                                MerchantOffer.source_product_id == product.source_product_id,
                            )
                            offer = (await self.session.scalars(offer_stmt)).first()
                            if offer:
                                offer.price_minor = int(product.price * 100)
                                offer.in_stock = product.in_stock
                                offer.last_synced_at = now
                        continue

                # Step E: Image pipeline (for new product)
                img_ref = ImageRef(url=str(product.image_url))
                try:
                    if not dry_run:
                        img_ref = process_image(
                            source.slug,
                            str(product.image_url),
                            client=self.client,
                            limiter=limiter,
                            storage=self.storage,
                            policy=source.image_policy,
                        )
                    counts["images_ok"] += 1
                except Exception:
                    counts["images_failed"] += 1

                # Step F: Deduplication evaluation
                category_name = taxonomy_category or product.source_category or "apparel"
                dedup_res = evaluate_dedup(
                    source_product_id=product.source_product_id,
                    item_group_id=product.item_group_id,
                    image_sha256=img_ref.sha256,
                    image_dhash=img_ref.dhash,
                    brand=product.brand,
                    category=category_name,
                    existing_records=dedup_records,
                )

                if dedup_res.action != "unique":
                    counts["deduped"] += 1

                # Step G: Insert new product
                counts["new"] += 1
                if not dry_run:
                    # Create or reuse CanonicalGarment
                    canonical_id: UUID
                    if dedup_res.canonical_id and dedup_res.action == "variant_group":
                        try:
                            canonical_id = UUID(dedup_res.canonical_id)
                        except ValueError:
                            garment = CanonicalGarment(
                                category=category_name,
                                subcategory=product.source_category,
                                tryon_supported=(source.rights_tryon and source.image_policy == "mirror"),
                            )
                            self.session.add(garment)
                            await self.session.flush()
                            canonical_id = garment.id
                    else:
                        garment = CanonicalGarment(
                            category=category_name,
                            subcategory=product.source_category,
                            tryon_supported=(source.rights_tryon and source.image_policy == "mirror"),
                        )
                        self.session.add(garment)
                        await self.session.flush()
                        canonical_id = garment.id

                    new_prod = MerchantProduct(
                        merchant_id=merchant.id,
                        source_id=source.id,
                        source_product_id=product.source_product_id,
                        item_group_id=product.item_group_id,
                        content_hash=content_hash,
                        status=product_status,
                        title=product.title,
                        description=product.description,
                        source_url=str(product.link),
                        last_seen_at=now,
                        price_checked_at=now,
                    )
                    self.session.add(new_prod)
                    existing_products[product.source_product_id] = new_prod

                    # Create MerchantOffer
                    offer = MerchantOffer(
                        garment_id=canonical_id,
                        merchant_id=merchant.id,
                        source_product_id=product.source_product_id,
                        url=str(product.link),
                        price_minor=int(product.price * 100),
                        currency="INR",
                        in_stock=product.in_stock,
                        last_synced_at=now,
                    )
                    self.session.add(offer)

                    # Store Image Record if mirrored
                    if img_ref.key and img_ref.sha256:
                        g_img = GarmentImage(
                            garment_id=canonical_id,
                            storage_key=img_ref.key,
                            content_hash=img_ref.sha256,
                            perceptual_hash=img_ref.dhash,
                            image_type="catalog",
                        )
                        self.session.add(g_img)

                    # Track in dedup list for subsequent rows
                    dedup_records.append(
                        {
                            "source_product_id": product.source_product_id,
                            "item_group_id": product.item_group_id,
                            "image_sha256": img_ref.sha256,
                            "image_dhash": img_ref.dhash,
                            "brand": product.brand,
                            "category": category_name,
                            "canonical_garment_id": str(canonical_id),
                        }
                    )

            # Step 5: Mass-removal guard check
            # If previous run had >= 10 products and seen count is < 50% of previous count:
            if previous_count >= 10 and len(seen_source_ids) < (0.5 * previous_count):
                run.status = "aborted"
                run.finished_at = datetime.now(UTC)
                run.error = f"mass_removal_guard: seen only {len(seen_source_ids)} products vs {previous_count} previous (<50%)"
                run.counts = dict(counts)
                run.counts["rejected"] = dict(counts["rejected"])
                await self.session.commit()
                return run

            # Step 6: Post-run stale & removal lifecycle (only for non-dry-run full runs)
            if not dry_run and not limit:
                stale_threshold = now - timedelta(hours=source.refresh_hours * 3)
                removed_threshold = now - timedelta(days=14)

                # Mark missing products older than grace period as stale
                for pid, prod_obj in existing_products.items():
                    if pid not in seen_source_ids and prod_obj.status == "active":
                        if prod_obj.last_seen_at and prod_obj.last_seen_at < stale_threshold:
                            prod_obj.status = "stale"
                            counts["stale_marked"] += 1

                    # Mark products stale for > 14 days as removed
                    if prod_obj.status == "stale":
                        if prod_obj.last_seen_at and prod_obj.last_seen_at < removed_threshold:
                            prod_obj.status = "removed"
                            counts["removed"] += 1

            # Complete successful run
            run.status = "ok"
            run.finished_at = datetime.now(UTC)
            run.counts = dict(counts)
            run.counts["rejected"] = dict(counts["rejected"])
            if not dry_run:
                await self.session.commit()
            return run

        except Exception as e:
            run.status = "failed"
            run.finished_at = datetime.now(UTC)
            run.error = str(e)
            run.counts = dict(counts)
            run.counts["rejected"] = dict(counts["rejected"])
            if not dry_run:
                await self.session.commit()
            raise
