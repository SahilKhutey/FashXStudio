from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from fashx.core.errors import ValidationError


@dataclass(frozen=True, slots=True)
class RecommendationContext:
    customer_id: UUID | None = None
    region: str | None = None
    currency: str = "INR"
    category: str | None = None
    brand: str | None = None
    style: str | None = None
    color: str | None = None
    material: str | None = None
    occasion: str | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    limit: int = 20
    exclude_product_ids: tuple[UUID, ...] = ()

    def validate(self) -> None:
        if self.limit < 1:
            raise ValidationError("Recommendation limit must be at least 1.")

        if self.limit > 100:
            raise ValidationError("Recommendation limit cannot exceed 100.")

        if self.min_price is not None and self.min_price < Decimal("0"):
            raise ValidationError("Minimum price cannot be negative.")

        if (
            self.min_price is not None
            and self.max_price is not None
            and self.max_price < self.min_price
        ):
            raise ValidationError(
                "Maximum price cannot be less than minimum price."
            )

        if len(self.currency) != 3:
            raise ValidationError("Currency must be a 3-character code.")
