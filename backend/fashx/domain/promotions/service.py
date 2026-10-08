from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.core.context import CoreContext
from app.core.errors import NotFoundError, ValidationError
from app.core.event_bus import EventBus
from fashx.domain.pricing.money import Money

from .entities import Offer, Promotion
from .enums import (
    DiscountType,
    OfferStatus,
    PromotionStatus,
)
from .events import (
    OfferCreated,
    OfferStatusChanged,
    PromotionApplied,
    PromotionCreated,
    PromotionStatusChanged,
)
from .lifecycle import (
    validate_offer_transition,
    validate_promotion_transition,
)
from .repository import (
    OfferRepository,
    PromotionRepository,
)


@dataclass(frozen=True, slots=True)
class OfferCalculation:
    base_price: Money
    discount: Money
    final_price: Money
    promotion_id: UUID
    offer_id: UUID


def calculate_discount(
    base_price: Money,
    discount_type: DiscountType,
    discount_value: Decimal,
    maximum_discount: Decimal | None = None,
) -> Money:
    if discount_value < 0:
        raise ValidationError("Discount value cannot be negative.")

    if discount_type == DiscountType.PERCENTAGE:
        if discount_value > 100:
            raise ValidationError("Percentage discount cannot exceed 100.")

        discount_amount = (
            base_price.amount * discount_value / Decimal("100")
        )
    else:
        discount_amount = discount_value

    if maximum_discount is not None:
        discount_amount = min(
            discount_amount,
            maximum_discount,
        )

    discount_amount = min(
        discount_amount,
        base_price.amount,
    )

    return Money(
        amount=discount_amount,
        currency=base_price.currency,
    )


class PromotionService:
    def __init__(
        self,
        promotion_repository: PromotionRepository,
        offer_repository: OfferRepository,
        event_bus: EventBus,
    ) -> None:
        self.promotion_repository = promotion_repository
        self.offer_repository = offer_repository
        self.event_bus = event_bus

    async def create_promotion(
        self,
        *,
        context: CoreContext,
        promotion: Promotion,
    ) -> Promotion:
        promotion.validate()

        await self.promotion_repository.save(promotion)

        await self.event_bus.publish(
            PromotionCreated(
                entity_id=promotion.id,
                correlation_id=context.correlation_id,
            )
        )

        return promotion

    async def get_promotion(
        self,
        promotion_id: UUID,
    ) -> Promotion:
        promotion = await self.promotion_repository.get(promotion_id)

        if promotion is None:
            raise NotFoundError(
                "Promotion was not found.",
                {"promotion_id": str(promotion_id)},
            )

        return promotion

    async def change_promotion_status(
        self,
        *,
        context: CoreContext,
        promotion_id: UUID,
        target: PromotionStatus,
    ) -> Promotion:
        promotion = await self.get_promotion(promotion_id)

        validate_promotion_transition(
            promotion.status,
            target,
        )

        promotion.status = target
        promotion.touch()

        await self.promotion_repository.save(promotion)

        await self.event_bus.publish(
            PromotionStatusChanged(
                entity_id=promotion.id,
                correlation_id=context.correlation_id,
            )
        )

        return promotion

    async def create_offer(
        self,
        *,
        context: CoreContext,
        offer: Offer,
    ) -> Offer:
        offer.validate()

        promotion = await self.get_promotion(offer.promotion_id)

        if promotion.status == PromotionStatus.ARCHIVED:
            raise ValidationError(
                "Archived promotion cannot receive new offers."
            )

        await self.offer_repository.save(offer)

        await self.event_bus.publish(
            OfferCreated(
                entity_id=offer.id,
                correlation_id=context.correlation_id,
            )
        )

        return offer

    async def change_offer_status(
        self,
        *,
        context: CoreContext,
        offer_id: UUID,
        target: OfferStatus,
    ) -> Offer:
        offer = await self.offer_repository.get(offer_id)

        if offer is None:
            raise NotFoundError(
                "Offer was not found.",
                {"offer_id": str(offer_id)},
            )

        validate_offer_transition(
            offer.status,
            target,
        )

        offer.status = target
        offer.touch()

        await self.offer_repository.save(offer)

        await self.event_bus.publish(
            OfferStatusChanged(
                entity_id=offer.id,
                correlation_id=context.correlation_id,
            )
        )

        return offer

    async def calculate_offer(
        self,
        *,
        context: CoreContext,
        offer_id: UUID,
        base_price: Money,
        purchase_value: Decimal | None = None,
    ) -> OfferCalculation:
        offer = await self.offer_repository.get(offer_id)

        if offer is None:
            raise NotFoundError(
                "Offer was not found.",
                {"offer_id": str(offer_id)},
            )

        if offer.status != OfferStatus.ACTIVE:
            return OfferCalculation(
                base_price=base_price,
                discount=Money(
                    Decimal("0"),
                    base_price.currency,
                ),
                final_price=base_price,
                promotion_id=offer.promotion_id,
                offer_id=offer.id,
            )

        promotion = await self.get_promotion(offer.promotion_id)

        if not promotion.is_effective():
            return OfferCalculation(
                base_price=base_price,
                discount=Money(
                    Decimal("0"),
                    base_price.currency,
                ),
                final_price=base_price,
                promotion_id=promotion.id,
                offer_id=offer.id,
            )

        if promotion.minimum_purchase_value is not None:
            if (
                purchase_value is None
                or purchase_value < promotion.minimum_purchase_value
            ):
                return OfferCalculation(
                    base_price=base_price,
                    discount=Money(
                        Decimal("0"),
                        base_price.currency,
                    ),
                    final_price=base_price,
                    promotion_id=promotion.id,
                    offer_id=offer.id,
                )

        discount = calculate_discount(
            base_price=base_price,
            discount_type=promotion.discount_type,
            discount_value=promotion.discount_value,
            maximum_discount=promotion.maximum_discount,
        )

        final_price = base_price.subtract(discount)

        result = OfferCalculation(
            base_price=base_price,
            discount=discount,
            final_price=final_price,
            promotion_id=promotion.id,
            offer_id=offer.id,
        )

        await self.event_bus.publish(
            PromotionApplied(
                entity_id=promotion.id,
                correlation_id=context.correlation_id,
            )
        )

        return result
