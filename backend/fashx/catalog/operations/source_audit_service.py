from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog_operations import (
    AuditActorRole,
    AuditOutcome,
    CatalogSourceAuditEvent,
)


class SourceAuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log_event(
        self,
        *,
        actor_id: UUID | None,
        actor_role: str = AuditActorRole.SYSTEM.value,
        merchant_id: UUID | None = None,
        source_id: UUID | None = None,
        entity_type: str,
        entity_id: str | None = None,
        action: str,
        safe_change_summary: dict | None = None,
        reason_code: str | None = None,
        request_id: str | None = None,
        outcome: str = AuditOutcome.SUCCESS.value,
    ) -> CatalogSourceAuditEvent:
        event = CatalogSourceAuditEvent(
            actor_id=actor_id,
            actor_role=actor_role,
            merchant_id=merchant_id,
            source_id=source_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            reason_code=reason_code,
            safe_change_summary=safe_change_summary or {},
            request_id=request_id,
            outcome=outcome,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_audit_events(
        self,
        *,
        merchant_id: UUID | None = None,
        source_id: UUID | None = None,
        entity_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CatalogSourceAuditEvent], int]:
        query = select(CatalogSourceAuditEvent)
        if merchant_id:
            query = query.where(CatalogSourceAuditEvent.merchant_id == merchant_id)
        if source_id:
            query = query.where(CatalogSourceAuditEvent.source_id == source_id)
        if entity_type:
            query = query.where(CatalogSourceAuditEvent.entity_type == entity_type)

        # Count total
        from sqlalchemy import func

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0

        # Fetch records
        query = query.order_by(desc(CatalogSourceAuditEvent.created_at)).offset(offset).limit(limit)
        result = await self.session.execute(query)
        events = list(result.scalars().all())
        return events, total
