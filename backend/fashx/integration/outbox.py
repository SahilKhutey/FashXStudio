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
