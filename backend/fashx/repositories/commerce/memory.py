from __future__ import annotations

from uuid import UUID

from fashx.core.errors import ConflictError
from fashx.domain.commerce.entities import (
    Brand,
    Marketplace,
    MarketplaceListing,
    ProductBrand,
    Seller,
)
from fashx.domain.commerce.repository import (
    BrandRepository,
    ListingRepository,
    MarketplaceRepository,
    ProductBrandRepository,
    SellerRepository,
)


class InMemoryBrandRepository(BrandRepository):

    def __init__(self) -> None:
        self._items: dict[UUID, Brand] = {}

    async def get(
        self,
        brand_id: UUID,
    ) -> Brand | None:
        return self._items.get(brand_id)

    async def get_by_slug(
        self,
        slug: str,
    ) -> Brand | None:

        normalized = slug.strip().lower()

        for item in self._items.values():
            if item.slug.lower() == normalized:
                return item

        return None

    async def save(
        self,
        brand: Brand,
    ) -> Brand:

        existing = await self.get_by_slug(brand.slug)

        if existing is not None and existing.id != brand.id:
            raise ConflictError(
                "Brand slug already exists.",
                {"slug": brand.slug},
            )

        self._items[brand.id] = brand
        return brand


class InMemorySellerRepository(SellerRepository):

    def __init__(self) -> None:
        self._items: dict[UUID, Seller] = {}

    async def get(
        self,
        seller_id: UUID,
    ) -> Seller | None:
        return self._items.get(seller_id)

    async def get_by_slug(
        self,
        slug: str,
    ) -> Seller | None:

        normalized = slug.strip().lower()

        for item in self._items.values():
            if item.slug.lower() == normalized:
                return item

        return None

    async def save(
        self,
        seller: Seller,
    ) -> Seller:

        existing = await self.get_by_slug(seller.slug)

        if existing is not None and existing.id != seller.id:
            raise ConflictError(
                "Seller slug already exists.",
                {"slug": seller.slug},
            )

        self._items[seller.id] = seller
        return seller


class InMemoryMarketplaceRepository(
    MarketplaceRepository
):

    def __init__(self) -> None:
        self._items: dict[UUID, Marketplace] = {}

    async def get(
        self,
        marketplace_id: UUID,
    ) -> Marketplace | None:
        return self._items.get(marketplace_id)

    async def get_by_slug(
        self,
        slug: str,
    ) -> Marketplace | None:

        normalized = slug.strip().lower()

        for item in self._items.values():
            if item.slug.lower() == normalized:
                return item

        return None

    async def save(
        self,
        marketplace: Marketplace,
    ) -> Marketplace:

        existing = await self.get_by_slug(
            marketplace.slug
        )

        if existing is not None and existing.id != marketplace.id:
            raise ConflictError(
                "Marketplace slug already exists.",
                {"slug": marketplace.slug},
            )

        self._items[marketplace.id] = marketplace
        return marketplace


class InMemoryProductBrandRepository(
    ProductBrandRepository
):

    def __init__(self) -> None:
        self._items: dict[UUID, ProductBrand] = {}

    async def get(
        self,
        product_id: UUID,
    ) -> ProductBrand | None:
        return self._items.get(product_id)

    async def save(
        self,
        relationship: ProductBrand,
    ) -> ProductBrand:

        self._items[
            relationship.product_id
        ] = relationship

        return relationship


class InMemoryListingRepository(
    ListingRepository
):

    def __init__(self) -> None:
        self._items: dict[
            UUID,
            MarketplaceListing,
        ] = {}

    async def get(
        self,
        listing_id: UUID,
    ) -> MarketplaceListing | None:
        return self._items.get(listing_id)

    async def save(
        self,
        listing: MarketplaceListing,
    ) -> MarketplaceListing:

        self._items[listing.id] = listing
        return listing

    async def list_by_product(
        self,
        product_id: UUID,
    ) -> list[MarketplaceListing]:

        return [
            item
            for item in self._items.values()
            if item.product_id == product_id
        ]

    async def list_by_seller(
        self,
        seller_id: UUID,
    ) -> list[MarketplaceListing]:

        return [
            item
            for item in self._items.values()
            if item.seller_id == seller_id
        ]
