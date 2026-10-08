from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fashx.core.events import DomainEvent


@dataclass(frozen=True, slots=True)
class PriceCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PriceCalculated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PricingRuleCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PricingRuleUpdated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PriceExpired(DomainEvent):
    entity_id: UUID | None = None
