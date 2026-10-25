"""Core acquisition pipeline processing normalized batches into FashXStudio catalog."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select

from database.models.catalog import (
    Brand,
    CanonicalGarment,
    GarmentImage,
    IngestRun,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from fashx.catalog.acquisition.contract import AcquisitionBatch
from fashx.catalog.acquisition.image_validator import SafeImageValidator
from fashx.catalog.acquisition.normalizer import CatalogNormalizer
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork


@dataclass
class PipelineRunReport:
    """Detailed metrics and outcome report for an acquisition run."""

    source_slug: str
    total_products: int = 0
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    rejected: int = 0
    rejection_reasons: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    ingest_run_id: UUID | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    success: bool = True

    def print_summary(self, apply: bool) -> None:
        mode_label = "APPLY (Production writes committed)" if apply else "DRY-RUN (Simulated without committing)"
        print("=" * 60)
        print(f"ACQUISITION PIPELINE REPORT [{self.source_slug.upper()}] - {mode_label}")
        print("=" * 60)
        print(f"Total Products Processed : {self.total_products}")
        print(f"Products Inserted        : {self.inserted}")
        print(f"Products Updated         : {self.updated}")
        print(f"Products Unchanged       : {self.unchanged}")
        print(f"Products Rejected        : {self.rejected}")
        print(f"Execution Status         : {'SUCCESS' if self.success else 'FAILED'}")
        if self.rejection_reasons:
            print("\nRejection Reasons:")
            for reason, count in self.rejection_reasons.items():
                print(f"  - {reason}: {count}")
        print("=" * 60)


class AcquisitionPipeline:
    """Validates, normalizes, deduplicates, and idempotently upserts source products."""

    def __init__(self, uow: CatalogUnitOfWork) -> None:
        self.uow = uow

    async def process_batch(
        self,
        batch: AcquisitionBatch,
        apply: bool = False,
        allow_unapproved_source: bool = False,
    ) -> PipelineRunReport:
        report = PipelineRunReport(
            source_slug=batch.source_slug,
            total_products=len(batch.products),
        )

        async with self.uow:
            # 1. Source verification: Sources must exist and be cleared for active feed ingestion
            source = await self.uow.sources.get_by_slug(batch.source_slug)
            if source is None:
                report.rejected = len(batch.products)
                report.rejection_reasons[f"unregistered_source_{batch.source_slug}"] = len(batch.products)
                report.success = False
                report.finished_at = datetime.now(UTC)
                return report

            if source.status != "cleared" and not allow_unapproved_source:
                report.rejected = len(batch.products)
                report.rejection_reasons[f"source_not_cleared_{source.status}"] = len(batch.products)
                report.success = False
                report.finished_at = datetime.now(UTC)
                return report

            now = datetime.now(UTC)
            merchants_by_name: dict[str, Merchant] = {}
            brands_by_name: dict[str, Brand] = {}

            for raw_p in batch.products:
                # 2. Normalization
                p = CatalogNormalizer.normalize_product(raw_p)

                if p.price_minor <= 0:
                    report.rejected += 1
                    report.rejection_reasons["invalid_or_zero_price"] += 1
                    continue

                # 3. Image validation & Rights evaluation
                perm_res = SafeImageValidator.evaluate_permissions(
                    image_url=p.image_url,
                    source_status=source.status,
                    source_rights_display=source.rights_display,
                    source_rights_tryon=source.rights_tryon,
                    source_image_policy=source.image_policy,
                    item_image_rights=p.image_rights,
                    item_tryon_rights=p.tryon_rights,
                )

                if not perm_res.is_valid:
                    report.rejected += 1
                    report.rejection_reasons[perm_res.error_reason or "invalid_image_url"] += 1
                    continue

                # 4. Merchant resolution
                m_name = p.brand or source.name
                if m_name not in merchants_by_name:
                    m = await self.uow.merchants.get_by_name(m_name)
                    if m is None:
                        m = Merchant(name=m_name, merchant_type="retailer")
                        self.uow.merchants.add(m)
                        await self.uow.merchants.flush()
                    merchants_by_name[m_name] = m
                merchant = merchants_by_name[m_name]

                # 5. Brand resolution
                brand_id: UUID | None = None
                if p.brand:
                    norm_b = p.brand.lower().replace(" ", "")
                    if norm_b not in brands_by_name:
                        stmt = select(Brand).where(Brand.normalized_name == norm_b)
                        b = (await self.uow.session.scalars(stmt)).first()
                        if b is None:
                            b = Brand(name=p.brand, normalized_name=norm_b)
                            self.uow.session.add(b)
                            await self.uow.session.flush()
                        brands_by_name[norm_b] = b
                    brand_id = brands_by_name[norm_b].id

                # 6. Deduplication & Idempotent Upsert
                existing_prod = await self.uow.merchant_products.get_by_source_id(
                    merchant.id, p.source_product_id
                )

                tryon_supported = perm_res.tryon_eligible

                if existing_prod is not None:
                    # Existing product: check if changed
                    existing_offer = await self.uow.offers.get_by_merchant_and_product(
                        merchant.id, p.source_product_id
                    )

                    is_price_changed = existing_offer and existing_offer.price_minor != p.price_minor
                    is_stock_changed = existing_offer and existing_offer.in_stock != p.in_stock

                    if is_price_changed or is_stock_changed or existing_prod.title != p.title:
                        # Update Offer
                        if existing_offer is not None:
                            existing_offer.price_minor = p.price_minor
                            existing_offer.in_stock = bool(p.in_stock)
                            existing_offer.last_synced_at = now

                        # Update MerchantProduct
                        existing_prod.title = p.title
                        existing_prod.description = p.description
                        existing_prod.source_url = p.product_url
                        existing_prod.last_seen_at = now
                        existing_prod.price_checked_at = now

                        # Update CanonicalGarment
                        if existing_prod.canonical_garment_id:
                            garment = await self.uow.canonical_garments.get_by_id(
                                existing_prod.canonical_garment_id
                            )
                            if garment is not None:
                                garment.display_name = p.title
                                garment.price_minor = p.price_minor
                                garment.in_stock = bool(p.in_stock)
                                garment.price_updated_at = now
                                garment.tryon_supported = tryon_supported
                                if p.sizes:
                                    garment.sizes_in_stock = list(p.sizes)

                        report.updated += 1
                    else:
                        # Unchanged product
                        existing_prod.last_seen_at = now
                        if existing_offer is not None:
                            existing_offer.last_synced_at = now
                        report.unchanged += 1

                else:
                    # New product
                    garment = CanonicalGarment(
                        brand_id=brand_id,
                        display_name=p.title,
                        category=p.category,
                        subcategory=p.subcategory,
                        price_minor=p.price_minor,
                        in_stock=bool(p.in_stock),
                        sizes_in_stock=list(p.sizes),
                        tryon_supported=tryon_supported,
                        price_updated_at=now,
                    )
                    self.uow.canonical_garments.add(garment)
                    await self.uow.canonical_garments.flush()

                    product = MerchantProduct(
                        merchant_id=merchant.id,
                        brand_id=brand_id,
                        canonical_garment_id=garment.id,
                        source_id=source.id,
                        source_product_id=p.source_product_id,
                        title=p.title,
                        description=p.description,
                        source_url=p.product_url,
                        last_seen_at=now,
                        price_checked_at=now,
                    )
                    self.uow.merchant_products.add(product)

                    offer = MerchantOffer(
                        garment_id=garment.id,
                        merchant_id=merchant.id,
                        source_product_id=p.source_product_id,
                        url=p.product_url,
                        price_minor=p.price_minor,
                        currency="INR",
                        in_stock=bool(p.in_stock),
                        last_synced_at=now,
                    )
                    self.uow.offers.add(offer)

                    # Persist image if display eligible
                    if p.image_url and perm_res.display_eligible:
                        content_hash = hashlib.sha256(p.image_url.encode("utf-8")).hexdigest()
                        img = GarmentImage(
                            garment_id=garment.id,
                            storage_key=p.image_url,
                            content_hash=content_hash,
                            image_type="primary",
                        )
                        self.uow.images.add(img)

                    report.inserted += 1

            # 7. Record IngestRun in audit trail
            report.finished_at = datetime.now(UTC)
            ingest_run = IngestRun(
                source_id=source.id,
                started_at=report.started_at,
                finished_at=report.finished_at,
                status="ok" if report.rejected < len(batch.products) else "failed",
                counts={
                    "total": report.total_products,
                    "inserted": report.inserted,
                    "updated": report.updated,
                    "unchanged": report.unchanged,
                    "rejected": report.rejected,
                    "rejection_reasons": dict(report.rejection_reasons),
                },
            )
            self.uow.ingest_runs.add(ingest_run)
            await self.uow.ingest_runs.flush()
            report.ingest_run_id = ingest_run.id

            if apply:
                await self.uow.commit()

        return report
