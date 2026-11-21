"""SA-019: Source health monitoring, diagnostics, and state transitions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CatalogSource
from database.models.catalog_sync import CatalogSyncRun
from fashx.catalog.acquisition.contracts_v2 import (
    SourceErrorCode,
    SourceHealthReport,
    SourceHealthState,
)
from fashx.catalog.acquisition.health import SourceHealthChecker


@pytest.mark.asyncio
async def test_sa_019_health_unknown_on_new_source(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    source_id = setup_authorized_source["source_id"]
    async with session_factory() as session:
        report = await SourceHealthChecker.evaluate_health(session, source_id)
        assert report.state == SourceHealthState.UNKNOWN
        assert "No sync runs recorded" in report.message


@pytest.mark.asyncio
async def test_sa_019_health_disabled_when_suspended(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    source_id = setup_authorized_source["source_id"]
    async with session_factory() as session:
        await session.execute(
            update(CatalogSource)
            .where(CatalogSource.id == source_id)
            .values(source_status="SUSPENDED")
        )
        await session.commit()

        report = await SourceHealthChecker.evaluate_health(session, source_id)
        assert report.state == SourceHealthState.DISABLED
        assert "SUSPENDED" in report.message


@pytest.mark.asyncio
async def test_sa_019_health_healthy_and_degraded_states(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    source_id = setup_authorized_source["source_id"]
    now = datetime.now(UTC)

    # 1. Record successful sync run
    async with session_factory() as session:
        run1 = CatalogSyncRun(
            id=uuid4(),
            source_id=source_id,
            mode="full",
            status="completed",
            started_at=now - timedelta(minutes=10),
            completed_at=now - timedelta(minutes=5),
            pages_fetched=2,
            products_seen=50,
            products_inserted=50,
        )
        session.add(run1)
        await session.commit()

        report = await SourceHealthChecker.evaluate_health(session, source_id)
        assert report.state == SourceHealthState.HEALTHY
        assert report.consecutive_failures == 0

    # 2. Record a failed sync run -> transitions to DEGRADED
    async with session_factory() as session:
        run2 = CatalogSyncRun(
            id=uuid4(),
            source_id=source_id,
            mode="full",
            status="failed",
            error_code=SourceErrorCode.TRANSIENT.value,
            started_at=now - timedelta(minutes=2),
            completed_at=now - timedelta(minutes=1),
        )
        session.add(run2)
        await session.commit()

        report = await SourceHealthChecker.evaluate_health(session, source_id)
        assert report.state == SourceHealthState.DEGRADED
        assert report.consecutive_failures == 1


@pytest.mark.asyncio
async def test_sa_019_health_auth_failed_and_rate_limited(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    source_id = setup_authorized_source["source_id"]
    now = datetime.now(UTC)

    # Auth failure state
    async with session_factory() as session:
        run_auth = CatalogSyncRun(
            id=uuid4(),
            source_id=source_id,
            mode="full",
            status="failed",
            error_code=SourceErrorCode.AUTHENTICATION.value,
            started_at=now - timedelta(minutes=2),
            completed_at=now - timedelta(minutes=1),
        )
        session.add(run_auth)
        await session.commit()

        report = await SourceHealthChecker.evaluate_health(session, source_id)
        assert report.state == SourceHealthState.AUTH_FAILED

    # Rate limited state
    async with session_factory() as session:
        run_rate = CatalogSyncRun(
            id=uuid4(),
            source_id=source_id,
            mode="incremental",
            status="failed",
            error_code=SourceErrorCode.RATE_LIMITED.value,
            started_at=now - timedelta(seconds=30),
            completed_at=now,
        )
        session.add(run_rate)
        await session.commit()

        report = await SourceHealthChecker.evaluate_health(session, source_id)
        assert report.state == SourceHealthState.RATE_LIMITED


@pytest.mark.asyncio
async def test_sa_019_perform_probe_diagnostic(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    source_id = setup_authorized_source["source_id"]

    async def mock_probe() -> SourceHealthReport:
        return SourceHealthReport(
            source_slug="test-feed",
            state=SourceHealthState.HEALTHY,
            message="Probe check OK",
        )

    async with session_factory() as session:
        report = await SourceHealthChecker.perform_probe(session, source_id, probe=mock_probe)
        assert report.state == SourceHealthState.HEALTHY
        assert "Probe check OK" in report.message

        # Verify last_authorization_check_at was updated on source
        src = (
            await session.execute(select(CatalogSource).where(CatalogSource.id == source_id))
        ).scalar_one()
        assert src.last_authorization_check_at is not None
