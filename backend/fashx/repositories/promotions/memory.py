from __future__ import annotations

from uuid import UUID

from app.core.errors import ConflictError
from fashx.domain.promotions.entities import (
    Offer,
    Promotion,
)
from fashx.domain.promotions.repository import (
    OfferRepository,
    PromotionRepository,
)


class InMemoryPromotionRepository(PromotionRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, Promotion] = {}

    async def get(
        self,
        promotion_id: UUID,
    ) -> Promotion | None:
        return self._items.get(promotion_id)

    async def get_by_code(
        self,
        code: str,
    ) -> Promotion | None:
        normalized = code.strip().lower()

        for item in self._items.values():
            if (
                item.code is not None
                and item.code.lower() == normalized
            ):
                return item

        return None

    async def save(
        self,
        promotion: Promotion,
    ) -> Promotion:
        if promotion.code:
            existing = await self.get_by_code(promotion.code)

            if existing is not None and existing.id != promotion.id:
                raise ConflictError(
                    "Promotion code already exists.",
                    {"code": promotion.code},
                )

        self._items[promotion.id] = promotion
        return promotion

    async def list_active(self) -> list[Promotion]:
        return [
            item
            for item in self._items.values()
            if item.is_effective()
        ]


class InMemoryOfferRepository(OfferRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, Offer] = {}

    async def get(
        self,
        offer_id: UUID,
    ) -> Offer | None:
        return self._items.get(offer_id)

    async def save(
        self,
        offer: Offer,
    ) -> Offer:
        self._items[offer.id] = offer
        return offer

    async def list_by_product(
        self,
        product_id: UUID,
    ) -> list[Offer]:
        return [
            item
            for item in self._items.values()
            if item.product_id == product_id
        ]

    async def list_by_variant(
        self,
        variant_id: UUID,
    ) -> list[Offer]:
        return [
            item
            for item in self._items.values()
            if item.variant_id == variant_id
        ]

    async def list_by_listing(
        self,
        listing_id: UUID,
    ) -> list[Offer]:
        return [
            item
            for item in self._items.values()
            if item.listing_id == listing_id
        ]
