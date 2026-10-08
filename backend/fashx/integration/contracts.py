from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from fashx.core.events import DomainEvent


@dataclass(frozen=True, slots=True)
class IntegrationMessage:
    message_id: UUID
    event: DomainEvent
    attempt: int = 0


class IntegrationHandler(ABC):
    @abstractmethod
    async def handle(
        self,
        message: IntegrationMessage,
    ) -> None:
        raise NotImplementedError
