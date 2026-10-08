from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from .entities import (
    Offer,
    Promotion,
)


class PromotionRepository(ABC):
    @abstractmethod
    async def get(
        self,
        promotion_id: UUID,
    ) -> Promotion | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_code(
        self,
        code: str,
    ) -> Promotion | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        promotion: Promotion,
    ) -> Promotion:
        raise NotImplementedError

    @abstractmethod
    async def list_active(
        self,
    ) -> list[Promotion]:
        raise NotImplementedError


class OfferRepository(ABC):
    @abstractmethod
    async def get(
        self,
        offer_id: UUID,
    ) -> Offer | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        offer: Offer,
    ) -> Offer:
        raise NotImplementedError

    @abstractmethod
    async def list_by_product(
        self,
        product_id: UUID,
    ) -> list[Offer]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_variant(
        self,
        variant_id: UUID,
    ) -> list[Offer]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_listing(
        self,
        listing_id: UUID,
    ) -> list[Offer]:
        raise NotImplementedError
