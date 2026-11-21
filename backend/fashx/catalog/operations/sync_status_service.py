from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource, IngestRun
from fashx.catalog.errors import CatalogAuthorizationError
from fashx.catalog.operations.schemas import SyncStatusDashboardResponse


class SyncStatusService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_source_sync_status(
        self,
        source_id: UUID,
        merchant_id: UUID | None = None,
    ) -> SyncStatusDashboardResponse:
        source = await self.session.get(CatalogSource, source_id)
        if not source:
            raise CatalogAuthorizationError(
                f"Catalog source '{source_id}' not found.",
                code="source_not_found",
            )
        if merchant_id and source.merchant_id != merchant_id:
            raise CatalogAuthorizationError(
                f"Access denied: source does not belong to merchant '{merchant_id}'.",
                code="tenant_isolation_violation",
            )

        # Get latest IngestRun
        latest_run = await self.session.scalar(
            select(IngestRun)
            .where(IngestRun.source_id == source_id)
            .order_by(desc(IngestRun.started_at))
            .limit(1)
        )

        last_sync_status = None
        last_sync_mode = None
        duration_seconds = None
        counts = {}
        last_error = None

        if latest_run:
            last_sync_status = latest_run.status
            last_sync_mode = latest_run.sync_mode
            counts = latest_run.counts or {}
            last_error = latest_run.error
            if latest_run.finished_at and latest_run.started_at:
                duration_seconds = max(
                    0.0,
                    (latest_run.finished_at - latest_run.started_at).total_seconds(),
                )

        is_healthy = (
            source.is_enabled
            and source.source_status not in ("SUSPENDED", "REVOKED")
            and (last_sync_status in ("ok", "completed", "running", None))
        )

        return SyncStatusDashboardResponse(
            source_id=source.id,
            source_name=source.name,
            operational_status=source.operational_status,
            source_status=source.source_status,
            last_sync_status=last_sync_status,
            last_sync_mode=last_sync_mode,
            last_successful_sync_at=source.last_successful_sync_at,
            last_failed_sync_at=source.last_failed_sync_at,
            duration_seconds=duration_seconds,
            counts=counts,
            last_error=last_error,
            is_healthy=is_healthy,
        )
