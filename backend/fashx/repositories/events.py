from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.commerce_feedback import DomainEvent


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        event_id: UUID,
        event_type: str,
        schema_version: int,
        user_id: UUID | None,
        object_type: str | None,
        object_id: UUID | None,
        trace_id: UUID | None,
        occurred_at: datetime,
        payload: dict[str, object],
    ) -> DomainEvent:
        event = DomainEvent(
            id=event_id,
            event_type=event_type,
            schema_version=schema_version,
            user_id=user_id,
            object_type=object_type,
            object_id=object_id,
            trace_id=trace_id,
            occurred_at=occurred_at,
            payload=payload,
        )
        self.session.add(event)
        await self.session.flush()
        return event
