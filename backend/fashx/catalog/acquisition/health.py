"""Source health monitoring, telemetry, and automated diagnostics."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource
from database.models.catalog_sync import CatalogSyncRun
from fashx.catalog.acquisition.contracts_v2 import (
    SourceErrorCode,
    SourceHealthReport,
    SourceHealthState,
)


class SourceHealthChecker:
    """Computes health states and executes lightweight diagnostics for catalog sources."""

    @classmethod
    async def evaluate_health(cls, session: AsyncSession, source_id: UUID) -> SourceHealthReport:
        # Load source
        src_res = await session.execute(select(CatalogSource).where(CatalogSource.id == source_id))
        source = src_res.scalar_one_or_none()
        if not source:
            return SourceHealthReport(
                source_slug="unknown",
                state=SourceHealthState.UNKNOWN,
                message=f"Source '{source_id}' not found.",
            )

        now = datetime.now(UTC)

        # 1. Disabled check
        if source.source_status in ("SUSPENDED", "REVOKED", "REJECTED"):
            return SourceHealthReport(
                source_slug=source.slug,
                state=SourceHealthState.DISABLED,
                last_check_at=source.last_authorization_check_at,
                last_successful_sync_at=source.last_successful_sync_at,
                message=f"Source is {source.source_status}.",
            )

        # 2. Check recent sync runs
        runs_stmt = (
            select(CatalogSyncRun)
            .where(CatalogSyncRun.source_id == source_id)
            .order_by(CatalogSyncRun.started_at.desc())
            .limit(5)
        )
        runs_res = await session.execute(runs_stmt)
        recent_runs = runs_res.scalars().all()

        if not recent_runs:
            return SourceHealthReport(
                source_slug=source.slug,
                state=SourceHealthState.UNKNOWN,
                last_check_at=source.last_authorization_check_at,
                message="No sync runs recorded yet.",
            )

        latest_run = recent_runs[0]
        consecutive_failures = sum(1 for r in recent_runs if r.status == "failed")

        # 3. Auth Failed check
        if latest_run.status == "failed" and latest_run.error_code in (
            SourceErrorCode.AUTHENTICATION.value,
            SourceErrorCode.AUTHORIZATION.value,
        ):
            return SourceHealthReport(
                source_slug=source.slug,
                state=SourceHealthState.AUTH_FAILED,
                last_check_at=source.last_authorization_check_at,
                last_failed_sync_at=latest_run.completed_at,
                consecutive_failures=consecutive_failures,
                message=f"Authentication/Authorization failed: {latest_run.error_code}",
            )

        # 4. Rate Limited check
        if (
            latest_run.status == "failed"
            and latest_run.error_code == SourceErrorCode.RATE_LIMITED.value
        ):
            return SourceHealthReport(
                source_slug=source.slug,
                state=SourceHealthState.RATE_LIMITED,
                last_check_at=source.last_authorization_check_at,
                last_failed_sync_at=latest_run.completed_at,
                consecutive_failures=consecutive_failures,
                message="Provider is throttling requests.",
            )

        # 5. Degraded check
        if consecutive_failures > 0:
            return SourceHealthReport(
                source_slug=source.slug,
                state=SourceHealthState.DEGRADED,
                last_check_at=source.last_authorization_check_at,
                last_failed_sync_at=latest_run.completed_at,
                consecutive_failures=consecutive_failures,
                message=f"{consecutive_failures} of last {len(recent_runs)} sync runs failed.",
            )

        # 6. Freshness / Stale check
        refresh_hours = getattr(source, "refresh_hours", 24) or 24
        stale_threshold = now - timedelta(hours=refresh_hours * 2)
        if source.last_successful_sync_at and source.last_successful_sync_at < stale_threshold:
            return SourceHealthReport(
                source_slug=source.slug,
                state=SourceHealthState.STALE,
                last_check_at=source.last_authorization_check_at,
                last_successful_sync_at=source.last_successful_sync_at,
                message=f"No successful sync within freshness window ({refresh_hours * 2} hours).",
            )

        return SourceHealthReport(
            source_slug=source.slug,
            state=SourceHealthState.HEALTHY,
            last_check_at=source.last_authorization_check_at,
            last_successful_sync_at=source.last_successful_sync_at,
            message="Source is healthy and operational.",
        )

    @classmethod
    async def perform_probe(
        cls,
        session: AsyncSession,
        source_id: UUID,
        adapter: Any = None,
        probe: Any = None,
    ) -> SourceHealthReport:
        """Lightweight live health check without downloading full catalog."""
        import asyncio

        t0 = time.time()
        now = datetime.now(UTC)

        # Update last authorization check timestamp
        stmt = select(CatalogSource).where(CatalogSource.id == source_id)
        res = await session.execute(stmt)
        source = res.scalar_one_or_none()
        if source:
            source.last_authorization_check_at = now
            await session.flush()

        if probe:
            res = probe()
            if asyncio.iscoroutine(res):
                report = await res
            else:
                report = res
        elif adapter and hasattr(adapter, "health_check"):
            report = await adapter.health_check()
        else:
            report = await cls.evaluate_health(session, source_id)

        report.latency_ms = (time.time() - t0) * 1000.0
        report.last_check_at = now
        return report
