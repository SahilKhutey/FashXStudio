"""Production synchronization engine orchestrating full snapshots and incremental updates."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CatalogSource, MerchantOffer
from fashx.catalog.acquisition.checkpoints import SyncCheckpointManager
from fashx.catalog.acquisition.contract import CatalogSourceAdapter
from fashx.catalog.acquisition.contracts_v2 import CatalogSourceAdapterV2, SyncMode
from fashx.catalog.acquisition.pagination import PaginationState
from fashx.catalog.acquisition.pipeline import AcquisitionPipeline, PipelineRunReport
from fashx.catalog.ingestion.authorization_guard import CatalogAuthorizationGuard
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork

logger = logging.getLogger(__name__)


class CatalogSyncEngine:
    """Executes full and incremental catalog synchronizations with durable checkpoints."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.session_factory = session_factory

    async def execute_sync(
        self,
        source_id: UUID,
        adapter: CatalogSourceAdapter | CatalogSourceAdapterV2,
        mode: SyncMode = SyncMode.FULL,
        limit_per_page: int = 100,
        apply: bool = True,
    ) -> PipelineRunReport:
        """Execute full or incremental synchronization for the given source and adapter."""
        async with self.session_factory() as session:
            # 1. Resolve source record
            src_res = await session.execute(
                select(CatalogSource).where(CatalogSource.id == source_id)
            )
            source_record = src_res.scalar_one_or_none()
            if not source_record:
                raise ValueError(f"CatalogSource '{source_id}' was not found in registry.")

            # 2. Authorization guard check: verify read and store permissions
            guard = CatalogAuthorizationGuard(session)
            await guard.guard_product_read(source_id)
            if apply:
                await guard.guard_product_store(source_id)

            # 3. Initialize sync run in database
            checkpoint_type = mode.value
            sync_run = await SyncCheckpointManager.record_sync_run_start(
                session, source_id=source_id, mode=mode.value
            )
            await session.commit()

        # 4. Load saved checkpoint
        async with self.session_factory() as session:
            saved_cp = await SyncCheckpointManager.load_checkpoint(
                session, source_id=source_id, checkpoint_type=checkpoint_type
            )
            initial_cursor = None
            watermark = None
            if saved_cp:
                if saved_cp.cursor_data and isinstance(saved_cp.cursor_data, dict):
                    initial_cursor = saved_cp.cursor_data.get("cursor")
                watermark = saved_cp.watermark

        pagination = PaginationState(current_cursor=initial_cursor, page_size=limit_per_page)
        seen_product_ids: set[str] = set()
        total_inserted = 0
        total_updated = 0
        total_rejected = 0
        all_success = True

        if hasattr(adapter, "start_incremental_sync") and mode == SyncMode.INCREMENTAL:
            await adapter.start_incremental_sync(watermark=watermark, cursor=initial_cursor)
        elif hasattr(adapter, "start_full_sync") and mode == SyncMode.FULL:
            await adapter.start_full_sync()

        uow = CatalogUnitOfWork(self.session_factory)
        pipeline = AcquisitionPipeline(uow)

        try:
            while pagination.has_more:
                # Fetch next page through adapter
                if hasattr(adapter, "fetch_page"):
                    batch = await adapter.fetch_page(
                        cursor=pagination.current_cursor, limit=limit_per_page
                    )  # type: ignore[union-attr]
                else:
                    batch = await adapter.fetch_batch(
                        cursor=pagination.current_cursor, limit=limit_per_page
                    )

                items_count = len(batch.products)
                for p in batch.products:
                    seen_product_ids.add(p.source_product_id)

                # Process batch through ingestion pipeline
                report = await pipeline.process_batch(batch, apply=apply)
                total_inserted += report.inserted
                total_updated += report.updated
                total_rejected += report.rejected

                if not report.success:
                    all_success = False

                # Advance pagination state
                pagination.advance(
                    next_cursor=batch.cursor,
                    has_more=batch.has_more,
                    items_count=items_count,
                )

                # Checkpoint persistence:
                # CRITICAL RULE: Database transaction containing product updates is committed,
                # then advance and persist the checkpoint record!
                async with self.session_factory() as session:
                    await SyncCheckpointManager.save_checkpoint(
                        session=session,
                        source_id=source_id,
                        checkpoint_type=checkpoint_type,
                        cursor_data={"cursor": pagination.current_cursor},
                        watermark=datetime.now(UTC),
                    )
                    await SyncCheckpointManager.update_sync_run_progress(
                        session=session,
                        run_id=sync_run.id,
                        pages_delta=1,
                        seen_delta=items_count,
                        inserted_delta=report.inserted,
                        updated_delta=report.updated,
                        rejected_delta=report.rejected,
                    )
                    await session.commit()

            # 5. Stale Reconciliation for FULL sync:
            # SAFEGUARD: Reconcile only if the FULL run completed successfully across all pages.
            # Never mark products out of stock after a partial or failed sync!
            if mode == SyncMode.FULL and all_success and apply and seen_product_ids:
                async with self.session_factory() as session:
                    # Mark offers not seen in this snapshot as out of stock
                    stale_stmt = (
                        update(MerchantOffer)
                        .where(
                            MerchantOffer.merchant_id == source_record.merchant_id,
                            MerchantOffer.source_product_id.not_in(seen_product_ids),
                            MerchantOffer.in_stock.is_(True),
                        )
                        .values(in_stock=False)
                    )
                    await session.execute(stale_stmt)
                    await session.commit()

            # 6. Mark run complete
            async with self.session_factory() as session:
                status = "completed" if all_success else "partial_failure"
                await SyncCheckpointManager.complete_sync_run(
                    session=session, run_id=sync_run.id, status=status
                )
                await session.commit()

        except Exception as exc:
            logger.error("Sync run %s failed with exception: %s", sync_run.id, exc, exc_info=True)
            async with self.session_factory() as session:
                await SyncCheckpointManager.complete_sync_run(
                    session=session,
                    run_id=sync_run.id,
                    status="failed",
                    error_code=str(exc)[:80],
                )
                await session.commit()
            raise

        return PipelineRunReport(
            source_slug=source_record.slug,
            success=all_success,
            total_products=len(seen_product_ids),
            inserted=total_inserted,
            updated=total_updated,
            rejected=total_rejected,
            finished_at=datetime.now(UTC),
        )
