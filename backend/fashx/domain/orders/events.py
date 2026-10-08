from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fashx.core.events import DomainEvent


@dataclass(frozen=True, slots=True)
class CheckoutCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CheckoutValidated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CheckoutCompleted(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class OrderCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class OrderStatusChanged(DomainEvent):
    entity_id: UUID | None = None
