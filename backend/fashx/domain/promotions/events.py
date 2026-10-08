from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fashx.core.events import DomainEvent


@dataclass(frozen=True, slots=True)
class PromotionCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PromotionStatusChanged(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class OfferCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class OfferStatusChanged(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PromotionApplied(DomainEvent):
    entity_id: UUID | None = None
