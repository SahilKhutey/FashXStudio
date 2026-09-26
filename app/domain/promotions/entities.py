from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.core.contracts import Entity
from app.core.errors import ValidationError
from app.core.ids import new_id

from .enums import (
    DiscountType,
    OfferStatus,
    PromotionScope,
    PromotionStatus,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Promotion(Entity):
    id: UUID = field(default_factory=new_id)
    name: str = ""
    code: str | None = None
    status: PromotionStatus = PromotionStatus.DRAFT
    scope: PromotionScope = PromotionScope.PRODUCT
    discount_type: DiscountType = DiscountType.PERCENTAGE
    discount_value: Decimal = Decimal("0")
    maximum_discount: Decimal | None = None
    minimum_purchase_value: Decimal | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    usage_limit: int | None = None
    per_customer_limit: int | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1

    def validate(self) -> None:
        if not self.name.strip():
            raise ValidationError("Promotion name cannot be empty.")

        if len(self.name) > 200:
            raise ValidationError(
                "Promotion name cannot exceed 200 characters."
            )

        if self.discount_value < 0:
            raise ValidationError("Discount value cannot be negative.")

        if (
            self.discount_type == DiscountType.PERCENTAGE
            and self.discount_value > 100
        ):
            raise ValidationError("Percentage discount cannot exceed 100.")

        if (
            self.maximum_discount is not None
            and self.maximum_discount < 0
        ):
            raise ValidationError("Maximum discount cannot be negative.")

        if (
            self.minimum_purchase_value is not None
            and self.minimum_purchase_value < 0
        ):
            raise ValidationError("Minimum purchase value cannot be negative.")

        if (
            self.start_at is not None
            and self.end_at is not None
            and self.end_at <= self.start_at
        ):
            raise ValidationError(
                "Promotion end must be after promotion start."
            )

        if self.usage_limit is not None and self.usage_limit < 1:
            raise ValidationError("Usage limit must be positive.")

        if (
            self.per_customer_limit is not None
            and self.per_customer_limit < 1
        ):
            raise ValidationError("Per-customer limit must be positive.")

        if self.version < 1:
            raise ValidationError("Promotion version must be positive.")

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1

    def is_effective(self, at: datetime | None = None) -> bool:
        now = at or utc_now()

        if self.status != PromotionStatus.ACTIVE:
            return False

        if self.start_at is not None and now < self.start_at:
            return False

        if self.end_at is not None and now >= self.end_at:
            return False

        return True


@dataclass(slots=True)
class Offer(Entity):
    id: UUID = field(default_factory=new_id)
    promotion_id: UUID | None = None
    product_id: UUID | None = None
    variant_id: UUID | None = None
    listing_id: UUID | None = None
    status: OfferStatus = OfferStatus.DRAFT
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if self.promotion_id is None:
            raise ValidationError("Offer requires a promotion ID.")

        targets = sum(
            target is not None
            for target in (
                self.product_id,
                self.variant_id,
                self.listing_id,
            )
        )

        if targets != 1:
            raise ValidationError(
                "Offer must target exactly one product, variant, or listing."
            )

        if self.version < 1:
            raise ValidationError("Offer version must be positive.")

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1
