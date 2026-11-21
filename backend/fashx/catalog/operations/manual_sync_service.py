from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource, IngestRun
from database.models.catalog_auth import CatalogSourceStatus
from database.models.catalog_operations import (
    AuditAction,
    AuditActorRole,
    AuditOutcome,
)
from fashx.catalog.errors import CatalogAuthorizationError
from fashx.catalog.operations.schemas import (
    ManualSyncRequest,
    ManualSyncResponse,
)
from fashx.catalog.operations.source_audit_service import SourceAuditService


class ManualSyncService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit_service = SourceAuditService(session)

    async def trigger_sync(
        self,
        source_id: UUID,
        payload: ManualSyncRequest,
        actor_id: UUID | None = None,
        actor_role: str = AuditActorRole.MERCHANT_OPERATOR.value,
        merchant_id: UUID | None = None,
    ) -> ManualSyncResponse:
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

        # Operational check
        if not source.is_enabled:
            raise CatalogAuthorizationError(
                f"Cannot trigger sync: source '{source.name}' is currently disabled.",
                code="source_disabled",
            )

        # Authorization check
        if source.source_status in (
            CatalogSourceStatus.SUSPENDED.value,
            CatalogSourceStatus.REVOKED.value,
        ):
            raise CatalogAuthorizationError(
                f"Cannot trigger sync: source authorization status is '{source.source_status}'.",
                code="source_not_authorized",
            )

        # Idempotency check: if idempotency_key was supplied, see if a run already exists
        if payload.idempotency_key:
            existing_run = await self.session.scalar(
                select(IngestRun).where(
                    IngestRun.source_id == source_id,
                    IngestRun.correlation_id == payload.idempotency_key,
                )
            )
            if existing_run:
                return ManualSyncResponse(
                    run_id=existing_run.id,
                    source_id=source_id,
                    sync_mode=existing_run.sync_mode or payload.sync_mode.value,
                    status=existing_run.status,
                    idempotency_key=payload.idempotency_key,
                    is_duplicate_request=True,
                    enqueued_at=existing_run.started_at,
                )

        # Rate limiting / concurrent job check
        now = datetime.now(UTC)
        if not payload.force:
            active_run = await self.session.scalar(
                select(IngestRun).where(
                    IngestRun.source_id == source_id,
                    IngestRun.status.in_(["running", "queued", "validating"]),
                )
            )
            if active_run:
                raise CatalogAuthorizationError(
                    f"A synchronization job ({active_run.id}) is already active for this source. Use force=True to override.",
                    code="sync_already_running",
                )

        # Create new IngestRun
        new_run = IngestRun(
            source_id=source.id,
            merchant_id=source.merchant_id,
            sync_mode=payload.sync_mode.value,
            correlation_id=payload.idempotency_key,
            status="queued",
            started_at=now,
            counts={"fetched": 0, "inserted": 0, "updated": 0, "quarantined": 0},
        )
        self.session.add(new_run)
        await self.session.flush()

        # Audit log
        await self.audit_service.log_event(
            actor_id=actor_id,
            actor_role=actor_role,
            merchant_id=source.merchant_id,
            source_id=source.id,
            entity_type="SYNC_RUN",
            entity_id=str(new_run.id),
            action=AuditAction.SYNC_TRIGGERED.value,
            reason_code="MANUAL_SYNC",
            safe_change_summary={
                "sync_mode": payload.sync_mode.value,
                "idempotency_key": payload.idempotency_key,
                "force": payload.force,
            },
            outcome=AuditOutcome.SUCCESS.value,
        )

        await self.session.commit()
        await self.session.refresh(new_run)

        return ManualSyncResponse(
            run_id=new_run.id,
            source_id=source_id,
            sync_mode=new_run.sync_mode or payload.sync_mode.value,
            status=new_run.status,
            idempotency_key=payload.idempotency_key,
            is_duplicate_request=False,
            enqueued_at=new_run.started_at,
        )
