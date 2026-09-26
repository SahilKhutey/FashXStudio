from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from .contracts import IntegrationMessage


class IdempotencyStore(ABC):
    @abstractmethod
    async def has_processed(
        self,
        consumer: str,
        message_id: UUID,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def mark_processed(
        self,
        consumer: str,
        message_id: UUID,
    ) -> None:
        raise NotImplementedError


class InMemoryIdempotencyStore(IdempotencyStore):
    def __init__(self) -> None:
        self._processed: set[tuple[str, UUID]] = set()

    async def has_processed(
        self,
        consumer: str,
        message_id: UUID,
    ) -> bool:
        return (consumer, message_id) in self._processed

    async def mark_processed(
        self,
        consumer: str,
        message_id: UUID,
    ) -> None:
        self._processed.add((consumer, message_id))


class IdempotentHandler:
    def __init__(
        self,
        *,
        consumer_name: str,
        handler: Any,
        store: IdempotencyStore,
    ) -> None:
        self.consumer_name = consumer_name
        self.handler = handler
        self.store = store

    async def handle(
        self,
        message: IntegrationMessage,
    ) -> None:
        processed = await self.store.has_processed(
            self.consumer_name,
            message.message_id,
        )

        if processed:
            return

        await self.handler.handle(message)

        await self.store.mark_processed(
            self.consumer_name,
            message.message_id,
        )
