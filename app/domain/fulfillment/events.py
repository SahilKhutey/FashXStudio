from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.core.events import DomainEvent


@dataclass(frozen=True, slots=True)
class FulfillmentCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class FulfillmentStatusChanged(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ShipmentCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ShipmentStatusChanged(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ShipmentDelivered(DomainEvent):
    entity_id: UUID | None = None
