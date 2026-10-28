"""Catalog synchronization service and stale offer reconciliation."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import IngestRun, MerchantOffer, MerchantProduct
from fashx.catalog.acquisition.pipeline import AcquisitionPipeline, PipelineRunReport
from fashx.catalog.acquisition.product_feed import normalize_product, read_csv_rows
from fashx.catalog.acquisition.registry import AdapterRegistry, get_adapter_registry
from fashx.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import EntityNotFoundError, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class CatalogSyncReport:
    source_id: str
    merchant_id: str
    total_rows: int = 0
    imported: int = 0
    failed: int = 0
    skipped: int = 0
    errors: list[dict[str, str | int]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class CatalogSyncService:
    """Orchestrates scheduled/triggered source synchronization and stale data reconciliation."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        registry: AdapterRegistry | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.registry = registry or get_adapter_registry()

    def _get_uow(self) -> CatalogUnitOfWork:
        return CatalogUnitOfWork(self.session_factory)

    async def sync_source(
        self,
        source_slug: str,
        limit: int = 100,
        apply: bool = False,
    ) -> PipelineRunReport:
        """Execute acquisition and synchronization for a single source adapter."""
        adapter = self.registry.get(source_slug)
        batch = await adapter.fetch_batch(limit=limit)

        uow = self._get_uow()
        pipeline = AcquisitionPipeline(uow)
        report = await pipeline.process_batch(batch, apply=apply)
        return report

    async def sync_all_sources(
        self,
        limit_per_source: int = 100,
        apply: bool = False,
    ) -> dict[str, PipelineRunReport]:
        """Synchronize all registered catalog source adapters with failure isolation."""
        reports: dict[str, PipelineRunReport] = {}
        sources = self.registry.list_sources()

        for slug in sources:
            try:
                report = await self.sync_source(slug, limit=limit_per_source, apply=apply)
                reports[slug] = report
            except Exception as exc:
                logger.error("Sync failed for source '%s': %s", slug, exc, exc_info=True)
                failed_report = PipelineRunReport(
                    source_slug=slug,
                    success=False,
                    rejection_reasons={f"adapter_exception: {exc}": 1},
                    finished_at=datetime.now(UTC),
                )
                reports[slug] = failed_report

        return reports

    async def reconcile_stale_offers(
        self,
        source_slug: str | None = None,
        stale_threshold_hours: int = 48,
        apply: bool = False,
    ) -> int:
        """Find active offers that have not been refreshed within threshold and mark them out of stock."""
        threshold_dt = datetime.now(UTC) - timedelta(hours=stale_threshold_hours)
        uow = self._get_uow()
        stale_count = 0

        async with uow:
            stmt = select(MerchantOffer).where(
                MerchantOffer.in_stock.is_(True),
                MerchantOffer.last_synced_at < threshold_dt,
            )

            if source_slug:
                source = await uow.sources.get_by_slug(source_slug)
                if source:
                    stmt = stmt.join(
                        MerchantProduct,
                        (MerchantProduct.merchant_id == MerchantOffer.merchant_id)
                        & (MerchantProduct.source_product_id == MerchantOffer.source_product_id),
                    ).where(MerchantProduct.source_id == source.id)

            offers: Sequence[MerchantOffer] = (await uow.session.scalars(stmt)).all()

            for offer in offers:
                offer.in_stock = False
                stale_count += 1

                # Reconcile CanonicalGarment if no other in-stock offers exist
                garment_id = offer.garment_id
                active_offers_stmt = select(MerchantOffer).where(
                    MerchantOffer.garment_id == garment_id,
                    MerchantOffer.id != offer.id,
                    MerchantOffer.in_stock.is_(True),
                )
                remaining_active = (await uow.session.scalars(active_offers_stmt)).first()
                if remaining_active is None:
                    garment = await uow.canonical_garments.get_by_id(garment_id)
                    if garment is not None:
                        garment.in_stock = False

            if apply and stale_count > 0:
                await uow.commit()

        return stale_count

    async def import_csv_feed(
        self,
        file_path: Path,
        source_id: UUID,
        merchant_id: UUID,
    ) -> CatalogSyncReport:
        """Import products from an approved CSV feed into FashXStudio catalog."""
        start_time = datetime.now(UTC)
        uow = self._get_uow()
        report = CatalogSyncReport(
            source_id=str(source_id),
            merchant_id=str(merchant_id),
        )

        async with uow:
            source = await uow.sources.get_by_id(source_id)
            if source is None:
                raise EntityNotFoundError("CatalogSource", source_id)
            if source.status != "cleared":
                raise ValidationError(
                    f"CatalogSource '{source.slug}' has status '{source.status}'; must be 'cleared' for product ingestion",
                    field="source_id",
                )
            if not source.rights_display:
                raise ValidationError(
                    f"CatalogSource '{source.slug}' does not have display rights enabled",
                    field="source_id",
                )

            merchant = await uow.merchants.get_by_id(merchant_id)
            if merchant is None:
                raise EntityNotFoundError("Merchant", merchant_id)

        ingest_uc = IngestMerchantProductUseCase(uow)

        for line_number, row in read_csv_rows(file_path):
            report.total_rows += 1
            try:
                norm_prod = normalize_product(row)
            except ValidationError as err:
                report.failed += 1
                report.errors.append({
                    "line": line_number,
                    "error": str(err),
                    "field": getattr(err, "field", "unknown"),
                })
                continue
            except Exception as exc:
                report.failed += 1
                report.errors.append({
                    "line": line_number,
                    "error": f"Normalization failure: {exc}",
                })
                continue

            try:
                cmd = IngestProductCommand(
                    merchant_id=merchant_id,
                    source_id=source_id,
                    source_product_id=norm_prod.source_product_id,
                    title=norm_prod.title,
                    source_url=norm_prod.source_url,
                    category=norm_prod.category,
                    subcategory=norm_prod.subcategory,
                    description=norm_prod.description,
                    price_minor=norm_prod.price_minor,
                    currency=norm_prod.currency,
                    in_stock=norm_prod.in_stock,
                    sizes_in_stock=list(norm_prod.sizes_in_stock),
                    brand_id=norm_prod.brand_id,
                    item_group_id=norm_prod.item_group_id,
                    content_hash=norm_prod.content_hash,
                    image_url=norm_prod.image_url,
                )
                await ingest_uc.execute(cmd)
                report.imported += 1
            except Exception as exc:
                logger.warning("Failed importing row %d: %s", line_number, exc)
                report.failed += 1
                report.errors.append({
                    "line": line_number,
                    "error": str(exc),
                })

        # Record durable ingestion history in database
        async with uow:
            run_status = "ok" if report.failed == 0 else "failed"
            ingest_run = IngestRun(
                source_id=source_id,
                started_at=start_time,
                finished_at=datetime.now(UTC),
                status=run_status,
                counts=report.to_dict(),
                error=f"{report.failed} errors encountered" if report.failed > 0 else None,
            )
            uow.ingest_runs.add(ingest_run)
            await uow.commit()

        return report
