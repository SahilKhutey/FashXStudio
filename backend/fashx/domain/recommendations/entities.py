from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

from fashx.core.errors import ValidationError
from fashx.core.ids import new_id

from .enums import RecommendationReason


@dataclass(slots=True)
class RecommendationCandidate:
    id: UUID = field(default_factory=new_id)
    product_id: UUID = field(default_factory=new_id)
    variant_id: UUID | None = None
    listing_id: UUID | None = None
    title: str = ""
    category: str | None = None
    brand: str | None = None
    style: str | None = None
    color: str | None = None
    material: str | None = None
    occasion: str | None = None
    price: Decimal | None = None
    currency: str = "INR"
    region: str | None = None
    source: str = "personalized"
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if self.product_id is None:
            raise ValidationError(
                "Recommendation candidate requires product_id."
            )

        if not self.title.strip():
            raise ValidationError(
                "Recommendation candidate requires title."
            )

        if self.price is not None and self.price < Decimal("0"):
            raise ValidationError("Candidate price cannot be negative.")

        if len(self.currency) != 3:
            raise ValidationError("Currency must be a 3-character code.")


@dataclass(frozen=True, slots=True)
class RecommendationExplanation:
    reason: RecommendationReason
    score: Decimal
    message: str


@dataclass(frozen=True, slots=True)
class RecommendationItem:
    product_id: UUID
    variant_id: UUID | None
    listing_id: UUID | None
    score: Decimal
    rank: int
    explanations: tuple[RecommendationExplanation, ...]


@dataclass(frozen=True, slots=True)
class RecommendationResult:
    items: tuple[RecommendationItem, ...]
    total_candidates: int
    engine_version: str = "1.0"
