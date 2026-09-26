from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.core.events import DomainEvent


@dataclass(frozen=True, slots=True)
class CartCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CartLineAdded(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CartLineQuantityChanged(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CartLineRemoved(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CartCleared(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CartStatusChanged(DomainEvent):
    entity_id: UUID | None = None
