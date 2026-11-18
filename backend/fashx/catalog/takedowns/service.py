from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource
from database.models.catalog_auth import (
    CatalogSourceStatus,
    CatalogTakedownRequest,
    TakedownStatus,
)
from fashx.catalog.errors import SourceNotFoundError, TakedownError
from fashx.catalog.takedowns.repository import CatalogTakedownRepository
from fashx.catalog.takedowns.schemas import (
    TakedownRequestCreate,
    TakedownResolutionRequest,
)


class CatalogTakedownService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CatalogTakedownRepository(session)

    async def initiate_takedown(self, payload: TakedownRequestCreate) -> CatalogTakedownRequest:
        # 1. Verify source exists
        source_res = await self.session.execute(
            select(CatalogSource).where(CatalogSource.id == payload.source_id)
        )
        source = source_res.scalar_one_or_none()
        if not source:
            raise SourceNotFoundError(payload.source_id)

        now = datetime.now(UTC)

        # 2. Immediately suspend source
        source.source_status = CatalogSourceStatus.SUSPENDED.value
        source.status = "suspended"
        source.rights_display = False
        source.rights_tryon = False

        # 3. Create takedown audit record
        takedown = CatalogTakedownRequest(
            source_id=payload.source_id,
            reason_code=payload.reason_code.value,
            requested_by=payload.requested_by,
            request_reference=payload.request_reference,
            status=TakedownStatus.SUSPENDED.value,
            received_at=now,
            acknowledged_at=now,
            assigned_reviewer=payload.assigned_reviewer,
            resolution_notes=payload.resolution_notes,
            affected_product_count=0,
            affected_asset_count=0,
        )
        created_takedown = await self.repo.create(takedown)
        await self.session.flush()
        return created_takedown

    async def triage_takedown(
        self, takedown_id: UUID, reviewer_id: UUID, notes: str | None = None
    ) -> CatalogTakedownRequest:
        takedown = await self.repo.get_by_id(takedown_id)
        if not takedown:
            raise TakedownError(f"Takedown request '{takedown_id}' not found.")

        takedown.status = TakedownStatus.PROCESSING.value
        takedown.assigned_reviewer = reviewer_id
        if notes:
            takedown.resolution_notes = notes
        return await self.repo.update(takedown)

    async def resolve_takedown(
        self, takedown_id: UUID, payload: TakedownResolutionRequest
    ) -> CatalogTakedownRequest:
        takedown = await self.repo.get_by_id(takedown_id)
        if not takedown:
            raise TakedownError(f"Takedown request '{takedown_id}' not found.")

        now = datetime.now(UTC)
        takedown.status = TakedownStatus.COMPLETED.value
        takedown.completed_at = now
        takedown.resolution_notes = payload.resolution_notes
        takedown.assigned_reviewer = payload.reviewer_id

        return await self.repo.update(takedown)

    async def get_takedown(self, takedown_id: UUID) -> CatalogTakedownRequest:
        takedown = await self.repo.get_by_id(takedown_id)
        if not takedown:
            raise TakedownError(f"Takedown request '{takedown_id}' not found.")
        return takedown

    async def list_by_source(self, source_id: UUID) -> Sequence[CatalogTakedownRequest]:
        return await self.repo.list_by_source(source_id)
