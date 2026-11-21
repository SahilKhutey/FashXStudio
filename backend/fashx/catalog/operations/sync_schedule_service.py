from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource
from database.models.catalog_operations import (
    AuditAction,
    AuditActorRole,
    AuditOutcome,
    CatalogSourceSchedule,
)
from fashx.catalog.errors import CatalogAuthorizationError
from fashx.catalog.operations.schemas import (
    SourceScheduleRequest,
    SourceScheduleResponse,
)
from fashx.catalog.operations.source_audit_service import SourceAuditService


class SyncScheduleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit_service = SourceAuditService(session)

    async def get_schedule(
        self,
        source_id: UUID,
        merchant_id: UUID | None = None,
    ) -> SourceScheduleResponse:
        schedule = await self.session.scalar(
            select(CatalogSourceSchedule).where(CatalogSourceSchedule.source_id == source_id)
        )
        if not schedule:
            raise CatalogAuthorizationError(
                f"Schedule for source '{source_id}' not found.",
                code="schedule_not_found",
            )
        if merchant_id and schedule.merchant_id != merchant_id:
            raise CatalogAuthorizationError(
                f"Access denied: source schedule does not belong to merchant '{merchant_id}'.",
                code="tenant_isolation_violation",
            )
        return SourceScheduleResponse.model_validate(schedule)

    async def update_schedule(
        self,
        source_id: UUID,
        payload: SourceScheduleRequest,
        actor_id: UUID | None = None,
        actor_role: str = AuditActorRole.MERCHANT_OPERATOR.value,
        merchant_id: UUID | None = None,
    ) -> SourceScheduleResponse:
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

        # Validate minimum interval of 15 minutes
        if payload.interval_minutes < 15:
            raise CatalogAuthorizationError(
                "Synchronization interval must be at least 15 minutes.",
                code="invalid_interval",
            )

        # Validate timezone
        try:
            ZoneInfo(payload.timezone)
        except Exception:
            raise CatalogAuthorizationError(
                f"Invalid timezone: '{payload.timezone}'.",
                code="invalid_timezone",
            )

        now = datetime.now(UTC)
        schedule = await self.session.scalar(
            select(CatalogSourceSchedule).where(CatalogSourceSchedule.source_id == source_id)
        )

        prev_config = {}
        if not schedule:
            schedule = CatalogSourceSchedule(
                source_id=source.id,
                merchant_id=source.merchant_id,
                enabled=payload.enabled,
                sync_mode=payload.sync_mode.value,
                interval_minutes=payload.interval_minutes,
                cron_expression=payload.cron_expression,
                timezone=payload.timezone,
                next_run_at=now + timedelta(minutes=payload.interval_minutes)
                if payload.enabled
                else None,
            )
            self.session.add(schedule)
        else:
            prev_config = {
                "enabled": schedule.enabled,
                "interval_minutes": schedule.interval_minutes,
                "sync_mode": schedule.sync_mode,
                "cron_expression": schedule.cron_expression,
            }
            schedule.enabled = payload.enabled
            schedule.sync_mode = payload.sync_mode.value
            schedule.interval_minutes = payload.interval_minutes
            schedule.cron_expression = payload.cron_expression
            schedule.timezone = payload.timezone
            schedule.updated_at = now
            if payload.enabled:
                schedule.next_run_at = now + timedelta(minutes=payload.interval_minutes)
            else:
                schedule.next_run_at = None

        await self.audit_service.log_event(
            actor_id=actor_id,
            actor_role=actor_role,
            merchant_id=source.merchant_id,
            source_id=source.id,
            entity_type="SCHEDULE",
            entity_id=str(schedule.id),
            action=AuditAction.SCHEDULE_UPDATED.value,
            safe_change_summary={
                "previous": prev_config,
                "new": {
                    "enabled": payload.enabled,
                    "interval_minutes": payload.interval_minutes,
                    "sync_mode": payload.sync_mode.value,
                    "timezone": payload.timezone,
                },
            },
            outcome=AuditOutcome.SUCCESS.value,
        )

        await self.session.commit()
        await self.session.refresh(schedule)

        return SourceScheduleResponse.model_validate(schedule)

    async def get_due_schedules(
        self,
        current_time: datetime | None = None,
    ) -> list[CatalogSourceSchedule]:
        now = current_time or datetime.now(UTC)
        query = (
            select(CatalogSourceSchedule)
            .join(CatalogSource, CatalogSource.id == CatalogSourceSchedule.source_id)
            .where(
                CatalogSourceSchedule.enabled.is_(True),
                CatalogSourceSchedule.next_run_at <= now,
                CatalogSource.is_enabled.is_(True),
            )
        )
        result = await self.session.execute(query)
        schedules = list(result.scalars().all())

        # Advance next_run_at
        for sched in schedules:
            sched.last_scheduled_at = now
            sched.next_run_at = now + timedelta(minutes=sched.interval_minutes)
            sched.updated_at = now

        await self.session.commit()
        return schedules
