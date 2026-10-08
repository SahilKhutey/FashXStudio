from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.core.events import DomainEvent


@dataclass(frozen=True, slots=True)
class StockLocationCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class InventoryCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class InventoryAdjusted(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class InventoryReserved(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class InventoryReleased(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class InventoryStatusChanged(DomainEvent):
    entity_id: UUID | None = None
