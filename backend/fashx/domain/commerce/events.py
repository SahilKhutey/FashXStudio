from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fashx.core.events import DomainEvent


@dataclass(frozen=True, slots=True)
class BrandCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class SellerCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class MarketplaceCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ProductBrandAssigned(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ListingCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ListingUpdated(DomainEvent):
    entity_id: UUID | None = None
