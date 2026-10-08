from dataclasses import dataclass
from uuid import UUID

from fashx.core.events import DomainEvent


@dataclass(frozen=True, slots=True)
class RecommendationsGenerated(DomainEvent):
    customer_id: UUID | None = None
    result_count: int = 0


@dataclass(frozen=True, slots=True)
class RecommendationViewed(DomainEvent):
    customer_id: UUID | None = None
    product_id: UUID | None = None
    rank: int = 0


@dataclass(frozen=True, slots=True)
class RecommendationSelected(DomainEvent):
    customer_id: UUID | None = None
    product_id: UUID | None = None
    rank: int = 0
