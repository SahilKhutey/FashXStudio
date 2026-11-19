from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource, IngestRun, MerchantOffer
from database.models.catalog_auth import CatalogSourceStatus
from database.models.catalog_image import CatalogImageAsset, ImageAssetStatus
from database.models.catalog_operations import (
    AuditAction,
    AuditActorRole,
    AuditOutcome,
    CatalogSourceSchedule,
    OperationalStatus,
)
from fashx.catalog.errors import CatalogAuthorizationError
from fashx.catalog.operations.schemas import (
    SourceTakedownRequest,
    SourceTakedownResponse,
)
from fashx.catalog.operations.source_audit_service import SourceAuditService


class SourceTakedownService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit_service = SourceAuditService(session)

    async def execute_takedown(
        self,
        source_id: UUID,
        payload: SourceTakedownRequest,
        actor_id: UUID | None = None,
        actor_role: str = AuditActorRole.PLATFORM_ADMIN.value,
    ) -> SourceTakedownResponse:
        source = await self.session.get(CatalogSource, source_id)
        if not source:
            raise CatalogAuthorizationError(
                f"Catalog source '{source_id}' not found.",
                code="source_not_found",
            )

        now = datetime.now(UTC)

        # 1. Immediately suspend source
        source.source_status = CatalogSourceStatus.SUSPENDED.value
        source.operational_status = OperationalStatus.SUSPENDED.value
        source.is_enabled = False
        source.updated_at = now

        # Disable schedule
        await self.session.execute(
            update(CatalogSourceSchedule)
            .where(CatalogSourceSchedule.source_id == source_id)
            .values(enabled=False, updated_at=now)
        )

        # 2. Abort all active/queued ingest jobs
        runs_query = select(IngestRun).where(
            IngestRun.source_id == source_id,
            IngestRun.status.in_(["running", "queued", "validating"]),
        )
        runs_res = await self.session.execute(runs_query)
        cancelled_jobs = 0
        for run in runs_res.scalars().all():
            run.status = "aborted"
            run.finished_at = now
            run.error = f"Aborted due to source takedown (reason: {payload.reason_code})"
            cancelled_jobs += 1

        # 3. Deactivate all merchant offers for this source
        offers_query = select(MerchantOffer).where(MerchantOffer.source_id == source_id)
        offers_res = await self.session.execute(offers_query)
        deactivated_offers = 0
        for offer in offers_res.scalars().all():
            offer.status = "SUSPENDED"
            offer.in_stock = False
            offer.updated_at = now
            deactivated_offers += 1

        # 4. Suspend/mark image assets if requested
        purged_images = 0
        if payload.purge_images:
            images_query = select(CatalogImageAsset).where(
                CatalogImageAsset.source_id == source_id,
                CatalogImageAsset.status != ImageAssetStatus.DELETED.value,
            )
            images_res = await self.session.execute(images_query)
            for img in images_res.scalars().all():
                img.status = ImageAssetStatus.SUSPENDED.value
                purged_images += 1

        # 5. Immutable audit event
        await self.audit_service.log_event(
            actor_id=actor_id,
            actor_role=actor_role,
            merchant_id=source.merchant_id,
            source_id=source.id,
            entity_type="TAKEDOWN",
            entity_id=str(source.id),
            action=AuditAction.TAKEDOWN_REQUESTED.value,
            reason_code=payload.reason_code,
            safe_change_summary={
                "reason_text": payload.reason_text,
                "purge_images": payload.purge_images,
                "jobs_cancelled": cancelled_jobs,
                "offers_deactivated": deactivated_offers,
                "images_suspended": purged_images,
            },
            outcome=AuditOutcome.SUCCESS.value,
        )

        await self.session.commit()

        return SourceTakedownResponse(
            source_id=source.id,
            takedown_status="COMPLETED",
            jobs_cancelled_count=cancelled_jobs,
            offers_deactivated_count=deactivated_offers,
            images_purged_count=purged_images,
            completed_at=now,
        )
