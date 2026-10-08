from dataclasses import dataclass
from uuid import UUID

from fashx.core.events import DomainEvent


@dataclass(frozen=True, slots=True)
class TrendObservationCreated(DomainEvent):
    entity_id: UUID | None = None
    topic: str = ""


@dataclass(frozen=True, slots=True)
class TrendCreated(DomainEvent):
    entity_id: UUID | None = None
    topic: str = ""


@dataclass(frozen=True, slots=True)
class TrendUpdated(DomainEvent):
    entity_id: UUID | None = None
    topic: str = ""


@dataclass(frozen=True, slots=True)
class TrendActivated(DomainEvent):
    entity_id: UUID | None = None
    topic: str = ""
