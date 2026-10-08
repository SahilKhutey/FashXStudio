from dataclasses import dataclass
from uuid import UUID

from app.core.events import DomainEvent


@dataclass(frozen=True, slots=True)
class OrderCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class OrderStatusChanged(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class OrderCancelled(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class OrderCompleted(DomainEvent):
    entity_id: UUID | None = None
