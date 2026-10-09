from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from fashx.core.events import DomainEvent


@dataclass(slots=True)
class OutboxMessage:
    id: UUID
    event: DomainEvent
    created_at: datetime
    published: bool = False
    attempts: int = 0


class OutboxRepository(ABC):
    @abstractmethod
    async def add(
        self,
        message: OutboxMessage,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def pending(
        self,
        limit: int = 100,
    ) -> list[OutboxMessage]:
        raise NotImplementedError

    @abstractmethod
    async def mark_published(
        self,
        message_id: UUID,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def claim(
        self,
        limit: int = 10,
        lease_seconds: int = 30,
    ) -> list[OutboxMessage]:
        raise NotImplementedError


class InMemoryOutboxRepository(OutboxRepository):
    def __init__(self) -> None:
        self._messages: dict[UUID, OutboxMessage] = {}

    async def add(
        self,
        message: OutboxMessage,
    ) -> None:
        self._messages[message.id] = message

    async def pending(
        self,
        limit: int = 100,
    ) -> list[OutboxMessage]:
        return [
            msg
            for msg in self._messages.values()
            if not msg.published
        ][:limit]

    async def mark_published(
        self,
        message_id: UUID,
    ) -> None:
        if message_id in self._messages:
            self._messages[message_id].published = True

    async def claim(
        self,
        limit: int = 10,
        lease_seconds: int = 30,
    ) -> list[OutboxMessage]:
        unpub = [msg for msg in self._messages.values() if not msg.published]
        for msg in unpub[:limit]:
            msg.attempts += 1
        return unpub[:limit]


class SqlOutboxRepository(OutboxRepository):
    """SQL-backed outbox repository supporting transactional publish and concurrent claiming."""

    def __init__(self, session: Any) -> None:
        self.session = session

    async def add(self, message: OutboxMessage) -> None:
        from database.models.operations import OutboxMessageRecord

        entity_type = getattr(message.event, "entity_type", "")
        payload = {
            "event_type": message.event.event_type,
            "entity_type": entity_type,
            "event_id": str(getattr(message.event, "event_id", message.id)),
        }
        record = OutboxMessageRecord(
            id=message.id,
            topic=message.event.event_type,
            payload=payload,
            created_at=message.created_at,
            published_at=datetime.now() if message.published else None,
            attempts=message.attempts,
        )
        self.session.add(record)
        await self.session.flush()

    async def pending(self, limit: int = 100) -> list[OutboxMessage]:
        from sqlalchemy import select
        from database.models.operations import OutboxMessageRecord

        stmt = (
            select(OutboxMessageRecord)
            .where(OutboxMessageRecord.published_at.is_(None))
            .order_by(OutboxMessageRecord.created_at)
            .limit(limit)
        )
        records = (await self.session.scalars(stmt)).all()
        return [self._to_message(r) for r in records]

    async def mark_published(self, message_id: UUID) -> None:
        from datetime import timezone
        from sqlalchemy import update
        from database.models.operations import OutboxMessageRecord

        now = datetime.now(timezone.utc)
        stmt = (
            update(OutboxMessageRecord)
            .where(OutboxMessageRecord.id == message_id)
            .values(published_at=now)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def claim(
        self,
        limit: int = 10,
        lease_seconds: int = 30,
    ) -> list[OutboxMessage]:
        from datetime import timedelta, timezone
        from sqlalchemy import select
        from database.models.operations import OutboxMessageRecord

        now = datetime.now(timezone.utc)
        stmt = (
            select(OutboxMessageRecord)
            .where(
                OutboxMessageRecord.published_at.is_(None),
                OutboxMessageRecord.next_attempt_at <= now,
            )
            .order_by(OutboxMessageRecord.created_at)
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
        records = (await self.session.scalars(stmt)).all()
        for r in records:
            r.attempts += 1
            r.next_attempt_at = now + timedelta(seconds=lease_seconds)
        await self.session.flush()
        return [self._to_message(r) for r in records]

    def _to_message(self, r: Any) -> OutboxMessage:
        from fashx.core.events import EntityCreated

        event_id = (
            UUID(r.payload["event_id"])
            if isinstance(r.payload, dict) and "event_id" in r.payload and r.payload["event_id"]
            else r.id
        )
        entity_type = (
            r.payload.get("entity_type", "") if isinstance(r.payload, dict) else ""
        )
        event = EntityCreated(event_id=event_id, entity_type=entity_type)
        return OutboxMessage(
            id=r.id,
            event=event,
            created_at=r.created_at,
            published=r.published_at is not None,
            attempts=r.attempts,
        )

