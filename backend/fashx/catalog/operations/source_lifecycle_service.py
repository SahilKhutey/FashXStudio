from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource, IngestRun
from database.models.catalog_auth import CatalogSourceStatus
from database.models.catalog_operations import (
    AuditAction,
    AuditActorRole,
    AuditOutcome,
    CatalogSourceSchedule,
    OperationalStatus,
)
from fashx.catalog.errors import CatalogAuthorizationError
from fashx.catalog.operations.schemas import (
    SourceOperationalStatusRequest,
    SourceOperationalStatusResponse,
)
from fashx.catalog.operations.source_audit_service import SourceAuditService


class SourceLifecycleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit_service = SourceAuditService(session)

    async def update_operational_status(
        self,
        source_id: UUID,
        payload: SourceOperationalStatusRequest,
        actor_id: UUID | None = None,
        actor_role: str = AuditActorRole.MERCHANT_OPERATOR.value,
        merchant_id: UUID | None = None,
    ) -> SourceOperationalStatusResponse:
        source = await self.session.get(CatalogSource, source_id)
        if not source:
            raise CatalogAuthorizationError(
                f"Catalog source '{source_id}' not found.",
                code="source_not_found",
            )

        # Enforce merchant tenant isolation
        if merchant_id and source.merchant_id != merchant_id:
            raise CatalogAuthorizationError(
                f"Access denied: source does not belong to merchant '{merchant_id}'.",
                code="tenant_isolation_violation",
            )

        # If source is revoked or suspended by platform admin, merchant cannot re-enable it
        if payload.target_status == OperationalStatus.ENABLED:
            if source.source_status in (
                CatalogSourceStatus.SUSPENDED.value,
                CatalogSourceStatus.REVOKED.value,
            ):
                raise CatalogAuthorizationError(
                    f"Cannot enable source with authorization status '{source.source_status}'. Administrative clearance required.",
                    code="source_authorization_blocked",
                )

        prev_status = source.operational_status
        new_is_enabled = payload.target_status == OperationalStatus.ENABLED

        source.operational_status = payload.target_status.value
        source.is_enabled = new_is_enabled
        source.updated_at = datetime.now(UTC)

        # Update schedule enabled flag to match
        await self.session.execute(
            update(CatalogSourceSchedule)
            .where(CatalogSourceSchedule.source_id == source_id)
            .values(enabled=new_is_enabled, updated_at=datetime.now(UTC))
        )

        # If disabling or pausing, abort any currently running or queued jobs
        jobs_aborted = 0
        if not new_is_enabled:
            running_runs_result = await self.session.execute(
                select(IngestRun).where(
                    IngestRun.source_id == source_id,
                    IngestRun.status.in_(["running", "queued", "validating"]),
                )
            )
            for run in running_runs_result.scalars().all():
                run.status = "aborted"
                run.finished_at = datetime.now(UTC)
                run.error = f"Aborted: source {payload.target_status.value} by operator (reason: {payload.reason})"
                jobs_aborted += 1

        # Audit log
        await self.audit_service.log_event(
            actor_id=actor_id,
            actor_role=actor_role,
            merchant_id=source.merchant_id,
            source_id=source.id,
            entity_type="SOURCE",
            entity_id=str(source.id),
            action=AuditAction.SOURCE_STATUS_CHANGED.value,
            reason_code="OPERATOR_STATUS_UPDATE",
            safe_change_summary={
                "previous_status": prev_status,
                "new_status": source.operational_status,
                "is_enabled": source.is_enabled,
                "reason": payload.reason,
                "jobs_aborted": jobs_aborted,
            },
            outcome=AuditOutcome.SUCCESS.value,
        )

        await self.session.commit()
        await self.session.refresh(source)

        return SourceOperationalStatusResponse(
            source_id=source.id,
            operational_status=source.operational_status,
            is_enabled=source.is_enabled,
            updated_at=source.updated_at,
            message=f"Source operational status set to {source.operational_status}. {jobs_aborted} running jobs aborted.",
        )
