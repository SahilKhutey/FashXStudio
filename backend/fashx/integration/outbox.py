from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

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
        message: OutboxMessage | str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
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
        message: OutboxMessage | str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        if isinstance(message, str):
            msg_id = uuid4()
            msg = OutboxMessage(
                id=msg_id,
                event=DomainEvent(event_id=msg_id),
                created_at=datetime.now(UTC),
            )
            msg.topic = message
            msg.payload = payload or {}
            self._messages[msg_id] = msg
            return msg
        else:
            self._messages[message.id] = message
            return message

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

    async def add(
        self,
        message: OutboxMessage | str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        from database.models.operations import OutboxMessageRecord

        if isinstance(message, str):
            record = OutboxMessageRecord(
                id=uuid4(),
                topic=message,
                payload=payload or {},
                created_at=datetime.now(UTC),
                attempts=0,
            )
            self.session.add(record)
            await self.session.flush()
            return record
        else:
            entity_type = getattr(message.event, "entity_type", "")
            data_payload = {
                "event_type": message.event.event_type,
                "entity_type": entity_type,
                "event_id": str(getattr(message.event, "event_id", message.id)),
            }
            if hasattr(message.event, "prefix"):
                data_payload["prefix"] = message.event.prefix
            if hasattr(message.event, "keys"):
                data_payload["keys"] = list(message.event.keys)
            record = OutboxMessageRecord(
                id=message.id,
                topic=message.event.event_type,
                payload=data_payload,
                created_at=message.created_at,
                published_at=datetime.now(UTC) if message.published else None,
                attempts=message.attempts,
            )
            self.session.add(record)
            await self.session.flush()
            return record

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
        from sqlalchemy import update

        from database.models.operations import OutboxMessageRecord

        now = datetime.now(UTC)
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
        from datetime import timedelta

        from sqlalchemy import select

        from database.models.operations import OutboxMessageRecord

        now = datetime.now(UTC)
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


async def run_outbox_worker_once(uow_or_session: Any, storage: Any) -> int:
    """Executes pending outbox tasks (such as storage.delete_keys and StoragePurgeRequested) and marks them published."""
    import inspect

    from sqlalchemy import select

    from database.models.operations import OutboxMessageRecord

    session = getattr(uow_or_session, "session", uow_or_session)
    stmt = (
        select(OutboxMessageRecord)
        .where(OutboxMessageRecord.published_at.is_(None))
        .order_by(OutboxMessageRecord.created_at)
    )
    records = (await session.scalars(stmt)).all()
    processed = 0
    now = datetime.now(UTC)

    for rec in records:
        topic = rec.topic
        payload = rec.payload or {}

        if topic in ("storage.delete_keys", "StorageDeleteKeysRequested"):
            keys = payload.get("keys", [])
            for k in keys:
                try:
                    res = storage.delete(k)
                    if inspect.isawaitable(res):
                        await res
                except Exception:
                    pass
            rec.published_at = now
            processed += 1
        elif topic in ("StoragePurgeRequested", "storage.purge_prefix"):
            prefix = payload.get("prefix", "")
            if prefix and hasattr(storage, "delete_prefix"):
                try:
                    res = storage.delete_prefix(prefix)
                    if inspect.isawaitable(res):
                        await res
                except Exception:
                    pass
            rec.published_at = now
            processed += 1

    await session.flush()
    return processed

