from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fashx.core.events import DomainEvent


@dataclass(frozen=True, slots=True)
class TaxonomyNodeCreated(DomainEvent):
    entity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ProductFashionClassificationChanged(
    DomainEvent
):
    entity_id: UUID | None = None
