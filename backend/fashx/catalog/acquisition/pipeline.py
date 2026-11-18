"""Core acquisition pipeline processing normalized batches into FashXStudio catalog."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import asdict, dataclass, field
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
from fashx.catalog.acquisition.normalizer import CatalogNormalizer, to_minor_units
from fashx.catalog.acquisition.quarantine import CatalogQuarantineService
from fashx.catalog.acquisition.record_validation import validate_product_record
from fashx.catalog.errors import PermissionDeniedError
from fashx.catalog.ingestion.authorization_guard import CatalogAuthorizationGuard
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork


@dataclass
class PipelineRunReport:
    """Detailed metrics and outcome report for an acquisition run."""

    source_slug: str
    source_id: UUID | None = None
    merchant_id: UUID | None = None
    total_products: int = 0
    validated: int = 0
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    rejected: int = 0
    quarantined: int = 0
    rejection_reasons: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    image_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    ingest_run_id: UUID | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    status: str = "COMPLETED"
    success: bool = True

    def print_summary(self, apply: bool) -> None:
        mode_label = (
            "APPLY (Production writes committed)"
            if apply
            else "DRY-RUN (Simulated without committing)"
        )
        print("=" * 60)
        print(f"ACQUISITION PIPELINE REPORT [{self.source_slug.upper()}] - {mode_label}")
        print("=" * 60)
        print(f"Total Products Processed : {self.total_products}")
        print(f"Products Validated       : {self.validated}")
        print(f"Products Inserted        : {self.inserted}")
        print(f"Products Updated         : {self.updated}")
        print(f"Products Unchanged       : {self.unchanged}")
        print(f"Products Rejected        : {self.rejected}")
        print(f"Products Quarantined     : {self.quarantined}")
        print(f"Execution Status         : {self.status} (success={self.success})")
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
        correlation_id: str | None = None,
        sync_mode: str = "incremental",
    ) -> PipelineRunReport:
        report = PipelineRunReport(
            source_slug=batch.source_slug,
            total_products=len(batch.products),
        )

        async with self.uow:
            # 1. Source verification: Sources must exist and be registered
            source = await self.uow.sources.get_by_slug(batch.source_slug)
            if source is None:
                report.rejected = len(batch.products)
                report.rejection_reasons[f"unregistered_source_{batch.source_slug}"] = len(
                    batch.products
                )
                report.status = "REJECTED"
                report.success = False
                report.finished_at = datetime.now(UTC)
                return report

            report.source_id = source.id

            # 2. Merchant resolution: Resolve merchant from registered source relationship
            merchant: Merchant | None = None
            if getattr(source, "merchant_id", None):
                merchant = await self.uow.merchants.get_by_id(source.merchant_id)
                if merchant is not None:
                    # Check merchant verification status
                    v_status = getattr(merchant, "verification_status", None)
                    if v_status in {"REJECTED", "SUSPENDED"}:
                        report.rejected = len(batch.products)
                        report.rejection_reasons["merchant_not_verified"] = len(batch.products)
                        report.status = "REJECTED"
                        report.success = False
                        report.finished_at = datetime.now(UTC)
                        return report
            if merchant is None:
                # Fallback to source.name for backwards compatibility
                m_name = source.name
                merchant = await self.uow.merchants.get_by_name(m_name)
                if merchant is None:
                    merchant = Merchant(
                        name=m_name, merchant_type=getattr(source, "kind", "retailer")
                    )
                    self.uow.merchants.add(merchant)
                    await self.uow.merchants.flush()

            report.merchant_id = merchant.id

            # 3. Source Status & Takedown checks
            source_status = getattr(source, "source_status", None)
            if source_status == "SUSPENDED":
                report.rejected = len(batch.products)
                report.rejection_reasons["source_suspended"] = len(batch.products)
                report.status = "REJECTED"
                report.success = False
                report.finished_at = datetime.now(UTC)
                return report

            if source_status == "EXPIRED":
                report.rejected = len(batch.products)
                report.rejection_reasons["source_expired"] = len(batch.products)
                report.status = "REJECTED"
                report.success = False
                report.finished_at = datetime.now(UTC)
                return report

            legacy_cleared = source.status == "cleared"
            active_cleared = source_status == "ACTIVE"

            if not (legacy_cleared or active_cleared) and not allow_unapproved_source:
                report.rejected = len(batch.products)
                report.rejection_reasons[f"source_not_cleared_{source.status}"] = len(
                    batch.products
                )
                report.status = "REJECTED"
                report.success = False
                report.finished_at = datetime.now(UTC)
                return report

            # 4. Granular Permission Checks (Phase 05.1 Evaluator Integration)
            if getattr(source, "merchant_id", None) and source_status == "ACTIVE":
                guard = CatalogAuthorizationGuard(self.uow.session)
                try:
                    await guard.guard_product_read(source.id, correlation_id=correlation_id)
                    if apply:
                        await guard.guard_product_store(source.id, correlation_id=correlation_id)
                except PermissionDeniedError as p_err:
                    err_code = getattr(
                        p_err, "reason_code", getattr(p_err, "code", "permission_denied")
                    )
                    report.rejected = len(batch.products)
                    report.rejection_reasons[f"permission_denied: {err_code}"] = len(batch.products)
                    report.status = "REJECTED"
                    report.success = False
                    report.finished_at = datetime.now(UTC)
                    return report

            # 5. Initialize IngestRun record
            now = datetime.now(UTC)
            ingest_run = IngestRun(
                source_id=source.id,
                merchant_id=merchant.id,
                sync_mode=sync_mode,
                correlation_id=correlation_id,
                started_at=report.started_at,
                status="RUNNING",
                counts={},
            )
            self.uow.ingest_runs.add(ingest_run)
            await self.uow.ingest_runs.flush()
            report.ingest_run_id = ingest_run.id

            quarantine_svc = CatalogQuarantineService(self.uow.session)
            brands_by_name: dict[str, Brand] = {}

            # 6. Process Records
            for raw_p in batch.products:
                # Step 6.1: Field validation
                val_res = validate_product_record(raw_p)
                if not val_res.valid:
                    primary_issue = val_res.issues[0]
                    safe_raw = (
                        asdict(raw_p)
                        if hasattr(raw_p, "__dataclass_fields__")
                        else {"title": getattr(raw_p, "title", None)}
                    )
                    await quarantine_svc.quarantine_record(
                        ingest_run_id=ingest_run.id,
                        source_id=source.id,
                        source_product_id=getattr(raw_p, "source_product_id", None),
                        reason_code=primary_issue.code,
                        field_name=primary_issue.field,
                        raw_record=safe_raw,
                        status="PENDING",
                    )
                    report.rejected += 1
                    report.quarantined += 1
                    report.rejection_reasons[primary_issue.code] += 1
                    continue

                # Step 6.2: Normalization
                # Category normalization
                cat_res = CatalogNormalizer.normalize_category_result(
                    raw_p.category, raw_p.title, raw_p.subcategory
                )
                if not cat_res.mapped or not cat_res.category:
                    safe_raw = (
                        asdict(raw_p)
                        if hasattr(raw_p, "__dataclass_fields__")
                        else {"title": getattr(raw_p, "title", None)}
                    )
                    await quarantine_svc.quarantine_record(
                        ingest_run_id=ingest_run.id,
                        source_id=source.id,
                        source_product_id=raw_p.source_product_id,
                        reason_code="category_unmapped",
                        field_name="category",
                        raw_record=safe_raw,
                        status="PENDING",
                    )
                    report.rejected += 1
                    report.quarantined += 1
                    report.rejection_reasons["category_unmapped"] += 1
                    continue

                category = cat_res.category
                subcategory = cat_res.subcategory

                # Price & Currency normalization
                currency = (raw_p.currency or "INR").upper().strip()
                try:
                    if isinstance(raw_p.price_minor, int):
                        if raw_p.price_minor <= 0:
                            raise ValueError("price_must_be_positive_and_finite")
                        price_minor = raw_p.price_minor
                    else:
                        price_minor = to_minor_units(raw_p.price_minor, currency)
                except Exception as p_err:
                    reason = "unsupported_currency" if "currency" in str(p_err) else "invalid_price"
                    safe_raw = (
                        asdict(raw_p)
                        if hasattr(raw_p, "__dataclass_fields__")
                        else {"title": getattr(raw_p, "title", None)}
                    )
                    await quarantine_svc.quarantine_record(
                        ingest_run_id=ingest_run.id,
                        source_id=source.id,
                        source_product_id=raw_p.source_product_id,
                        reason_code=reason,
                        field_name="price_minor",
                        raw_record=safe_raw,
                        status="PENDING",
                    )
                    report.rejected += 1
                    report.quarantined += 1
                    report.rejection_reasons[reason] += 1
                    continue

                # Brand normalization
                brand_name = CatalogNormalizer.normalize_brand(raw_p.brand, raw_p.title)
                brand_id: UUID | None = None
                if brand_name:
                    norm_b = brand_name.lower().replace(" ", "")
                    if norm_b not in brands_by_name:
                        stmt = select(Brand).where(Brand.normalized_name == norm_b)
                        b = (await self.uow.session.scalars(stmt)).first()
                        if b is None:
                            b = Brand(name=brand_name, normalized_name=norm_b)
                            self.uow.session.add(b)
                            await self.uow.session.flush()
                        brands_by_name[norm_b] = b
                    brand_id = brands_by_name[norm_b].id

                # Size & URL normalization
                sizes = CatalogNormalizer.normalize_sizes(raw_p.sizes)
                product_url = CatalogNormalizer.sanitize_url(
                    raw_p.product_url, preserve_affiliate=True
                )
                in_stock = raw_p.in_stock

                # Product passed validation & normalization
                report.validated += 1

                # Step 6.3: Image validation & Rights evaluation
                perm_res = SafeImageValidator.evaluate_permissions(
                    image_url=raw_p.image_url,
                    source_status=source.status,
                    source_rights_display=source.rights_display,
                    source_rights_tryon=source.rights_tryon,
                    source_image_policy=source.image_policy,
                    item_image_rights=raw_p.image_rights,
                    item_tryon_rights=raw_p.tryon_rights,
                )

                if raw_p.image_url:
                    if perm_res.is_valid and perm_res.display_eligible:
                        report.image_counts["permitted"] += 1
                    else:
                        report.image_counts["skipped_by_permission"] += 1
                else:
                    report.image_counts["missing"] += 1

                display_eligible = perm_res.display_eligible
                tryon_supported = perm_res.tryon_eligible

                # Step 6.4: Deterministic content hash
                content_hash = hashlib.sha256(
                    f"{raw_p.source_product_id}|{raw_p.title}|{brand_name or ''}|"
                    f"{category}|{subcategory or ''}|{price_minor}|{currency}|"
                    f"{product_url}|{in_stock}|{','.join(sizes)}".encode()
                ).hexdigest()

                # Step 6.5: Deduplication & Idempotent Upsert
                existing_prod = await self.uow.merchant_products.get_by_source_id(
                    merchant.id, raw_p.source_product_id
                )

                if existing_prod is not None:
                    existing_offer = await self.uow.offers.get_by_merchant_and_product(
                        merchant.id, raw_p.source_product_id
                    )

                    is_hash_changed = existing_prod.content_hash != content_hash
                    is_price_changed = (
                        existing_offer is not None and existing_offer.price_minor != price_minor
                    )
                    is_stock_changed = existing_offer is not None and existing_offer.in_stock != (
                        bool(in_stock) if in_stock is not None else False
                    )
                    is_title_changed = existing_prod.title != raw_p.title

                    if is_hash_changed or is_price_changed or is_stock_changed or is_title_changed:
                        # Update Offer
                        if existing_offer is not None:
                            existing_offer.price_minor = price_minor
                            existing_offer.currency = currency
                            existing_offer.in_stock = (
                                bool(in_stock) if in_stock is not None else False
                            )
                            existing_offer.last_synced_at = now
                            existing_offer.url = product_url

                        # Update MerchantProduct
                        existing_prod.title = raw_p.title
                        existing_prod.description = raw_p.description
                        existing_prod.source_url = product_url
                        existing_prod.brand_id = brand_id
                        existing_prod.content_hash = content_hash
                        existing_prod.last_seen_at = now
                        existing_prod.price_checked_at = now

                        # Update CanonicalGarment
                        if existing_prod.canonical_garment_id:
                            garment = await self.uow.canonical_garments.get_by_id(
                                existing_prod.canonical_garment_id
                            )
                            if garment is not None:
                                garment.display_name = raw_p.title
                                garment.price_minor = price_minor
                                garment.category = category
                                garment.subcategory = subcategory
                                garment.in_stock = bool(in_stock) if in_stock is not None else False
                                garment.price_updated_at = now
                                garment.tryon_supported = tryon_supported
                                garment.sizes_in_stock = list(sizes)

                        # Update or add prepared image if permitted
                        if (
                            raw_p.prepared_image_key
                            and raw_p.prepared_image_hash
                            and display_eligible
                            and existing_prod.canonical_garment_id
                        ):
                            existing_imgs = await self.uow.images.list_for_garment(
                                existing_prod.canonical_garment_id
                            )
                            has_img = any(
                                img.content_hash == raw_p.prepared_image_hash
                                for img in existing_imgs
                            )
                            if not has_img:
                                new_img = GarmentImage(
                                    garment_id=existing_prod.canonical_garment_id,
                                    storage_key=raw_p.prepared_image_key,
                                    content_hash=raw_p.prepared_image_hash,
                                    image_type="primary",
                                )
                                self.uow.images.add(new_img)
                                report.image_counts["stored"] += 1

                        report.updated += 1
                    else:
                        existing_prod.last_seen_at = now
                        if existing_offer is not None:
                            existing_offer.last_synced_at = now
                        report.unchanged += 1

                else:
                    # New product insert
                    garment = CanonicalGarment(
                        brand_id=brand_id,
                        display_name=raw_p.title,
                        category=category,
                        subcategory=subcategory,
                        price_minor=price_minor,
                        in_stock=bool(in_stock) if in_stock is not None else False,
                        sizes_in_stock=list(sizes),
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
                        source_product_id=raw_p.source_product_id,
                        content_hash=content_hash,
                        title=raw_p.title,
                        description=raw_p.description,
                        source_url=product_url,
                        last_seen_at=now,
                        price_checked_at=now,
                    )
                    self.uow.merchant_products.add(product)

                    offer = MerchantOffer(
                        garment_id=garment.id,
                        merchant_id=merchant.id,
                        source_product_id=raw_p.source_product_id,
                        url=product_url,
                        price_minor=price_minor,
                        currency=currency,
                        in_stock=bool(in_stock) if in_stock is not None else False,
                        last_synced_at=now,
                    )
                    self.uow.offers.add(offer)

                    # Persist image if display eligible
                    if raw_p.prepared_image_key and raw_p.prepared_image_hash and display_eligible:
                        img = GarmentImage(
                            garment_id=garment.id,
                            storage_key=raw_p.prepared_image_key,
                            content_hash=raw_p.prepared_image_hash,
                            image_type="primary",
                        )
                        self.uow.images.add(img)
                        report.image_counts["stored"] += 1
                    elif raw_p.image_url and display_eligible:
                        img_hash = hashlib.sha256(raw_p.image_url.encode("utf-8")).hexdigest()
                        img = GarmentImage(
                            garment_id=garment.id,
                            storage_key=raw_p.image_url,
                            content_hash=img_hash,
                            image_type="primary",
                        )
                        self.uow.images.add(img)
                        report.image_counts["stored"] += 1

                    report.inserted += 1

            # 7. Record IngestRun completion
            report.finished_at = datetime.now(UTC)
            if report.rejected == report.total_products and report.total_products > 0:
                terminal_status = "REJECTED"
                report.success = False
            elif report.quarantined > 0 or report.rejected > 0:
                terminal_status = "PARTIAL"
                report.success = True
            else:
                terminal_status = "COMPLETED"
                report.success = True

            report.status = terminal_status
            ingest_run.status = terminal_status
            ingest_run.finished_at = report.finished_at
            ingest_run.counts = {
                "total": report.total_products,
                "validated": report.validated,
                "inserted": report.inserted,
                "updated": report.updated,
                "unchanged": report.unchanged,
                "rejected": report.rejected,
                "quarantined": report.quarantined,
                "rejection_reasons": dict(report.rejection_reasons),
                "image_counts": dict(report.image_counts),
            }

            if apply:
                await self.uow.commit()

        return report
