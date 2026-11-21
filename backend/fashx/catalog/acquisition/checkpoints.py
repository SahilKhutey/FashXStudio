"""Durable checkpoint persistence and synchronization run tracking."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog_sync import CatalogSyncCheckpoint, CatalogSyncRun


class SyncCheckpointManager:
    """Manages transactional checkpoint records and sync execution metrics."""

    @classmethod
    async def load_checkpoint(
        cls, session: AsyncSession, source_id: UUID, checkpoint_type: str
    ) -> CatalogSyncCheckpoint | None:
        stmt = select(CatalogSyncCheckpoint).where(
            CatalogSyncCheckpoint.source_id == source_id,
            CatalogSyncCheckpoint.checkpoint_type == checkpoint_type,
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def save_checkpoint(
        cls,
        session: AsyncSession,
        source_id: UUID,
        checkpoint_type: str,
        cursor_data: dict | None = None,
        watermark: datetime | None = None,
        provider_version: str | None = None,
    ) -> CatalogSyncCheckpoint:
        """Persist cursor and watermark.

        Note: Callers must commit product records prior to or alongside this update.
        """
        stmt = select(CatalogSyncCheckpoint).where(
            CatalogSyncCheckpoint.source_id == source_id,
            CatalogSyncCheckpoint.checkpoint_type == checkpoint_type,
        )
        res = await session.execute(stmt)
        record = res.scalar_one_or_none()
        now = datetime.now(UTC)

        if record is None:
            record = CatalogSyncCheckpoint(
                id=uuid4(),
                source_id=source_id,
                checkpoint_type=checkpoint_type,
                cursor_data=cursor_data,
                watermark=watermark,
                provider_version=provider_version,
                last_success_at=now,
                updated_at=now,
            )
            session.add(record)
        else:
            record.cursor_data = cursor_data
            if watermark is not None:
                record.watermark = watermark
            if provider_version is not None:
                record.provider_version = provider_version
            record.last_success_at = now
            record.updated_at = now

        await session.flush()
        return record

    @classmethod
    async def record_sync_run_start(
        cls,
        session: AsyncSession,
        source_id: UUID,
        mode: str,
        snapshot_id: str | None = None,
    ) -> CatalogSyncRun:
        run = CatalogSyncRun(
            id=uuid4(),
            source_id=source_id,
            mode=mode,
            status="running",
            snapshot_id=snapshot_id,
            started_at=datetime.now(UTC),
            pages_fetched=0,
            products_seen=0,
            products_inserted=0,
            products_updated=0,
            products_rejected=0,
        )
        session.add(run)
        await session.flush()
        return run

    @classmethod
    async def update_sync_run_progress(
        cls,
        session: AsyncSession,
        run_id: UUID,
        pages_delta: int = 0,
        seen_delta: int = 0,
        inserted_delta: int = 0,
        updated_delta: int = 0,
        rejected_delta: int = 0,
    ) -> CatalogSyncRun | None:
        stmt = select(CatalogSyncRun).where(CatalogSyncRun.id == run_id)
        res = await session.execute(stmt)
        run = res.scalar_one_or_none()
        if run:
            run.pages_fetched += pages_delta
            run.products_seen += seen_delta
            run.products_inserted += inserted_delta
            run.products_updated += updated_delta
            run.products_rejected += rejected_delta
            await session.flush()
        return run

    @classmethod
    async def complete_sync_run(
        cls,
        session: AsyncSession,
        run_id: UUID,
        status: str = "completed",
        error_code: str | None = None,
    ) -> CatalogSyncRun | None:
        stmt = select(CatalogSyncRun).where(CatalogSyncRun.id == run_id)
        res = await session.execute(stmt)
        run = res.scalar_one_or_none()
        if run:
            run.status = status
            run.completed_at = datetime.now(UTC)
            run.error_code = error_code
            await session.flush()
        return run
