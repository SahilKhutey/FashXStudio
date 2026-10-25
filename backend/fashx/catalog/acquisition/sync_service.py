"""Catalog synchronization service and stale offer reconciliation."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import MerchantOffer, MerchantProduct
from fashx.catalog.acquisition.pipeline import AcquisitionPipeline, PipelineRunReport
from fashx.catalog.acquisition.registry import AdapterRegistry, get_adapter_registry
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork

logger = logging.getLogger(__name__)


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
