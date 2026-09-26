from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """
    Base event exchanged between FashXStudio core systems.
    """

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    correlation_id: UUID | None = None
    causation_id: UUID | None = None

    @property
    def event_type(self) -> str:
        return self.__class__.__name__


@dataclass(frozen=True, slots=True)
class EntityCreated(DomainEvent):
    entity_type: str = ""
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class EntityUpdated(DomainEvent):
    entity_type: str = ""
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class EntityDeleted(DomainEvent):
    entity_type: str = ""
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    event: DomainEvent
    metadata: dict[str, Any] = field(default_factory=dict)
