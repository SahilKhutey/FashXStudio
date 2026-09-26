from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from .entities import (
    Brand,
    Marketplace,
    MarketplaceListing,
    ProductBrand,
    Seller,
)


class BrandRepository(ABC):

    @abstractmethod
    async def get(
        self,
        brand_id: UUID,
    ) -> Brand | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_slug(
        self,
        slug: str,
    ) -> Brand | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        brand: Brand,
    ) -> Brand:
        raise NotImplementedError


class SellerRepository(ABC):

    @abstractmethod
    async def get(
        self,
        seller_id: UUID,
    ) -> Seller | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_slug(
        self,
        slug: str,
    ) -> Seller | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        seller: Seller,
    ) -> Seller:
        raise NotImplementedError


class MarketplaceRepository(ABC):

    @abstractmethod
    async def get(
        self,
        marketplace_id: UUID,
    ) -> Marketplace | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_slug(
        self,
        slug: str,
    ) -> Marketplace | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        marketplace: Marketplace,
    ) -> Marketplace:
        raise NotImplementedError


class ProductBrandRepository(ABC):

    @abstractmethod
    async def get(
        self,
        product_id: UUID,
    ) -> ProductBrand | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        relationship: ProductBrand,
    ) -> ProductBrand:
        raise NotImplementedError


class ListingRepository(ABC):

    @abstractmethod
    async def get(
        self,
        listing_id: UUID,
    ) -> MarketplaceListing | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        listing: MarketplaceListing,
    ) -> MarketplaceListing:
        raise NotImplementedError

    @abstractmethod
    async def list_by_product(
        self,
        product_id: UUID,
    ) -> list[MarketplaceListing]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_seller(
        self,
        seller_id: UUID,
    ) -> list[MarketplaceListing]:
        raise NotImplementedError
