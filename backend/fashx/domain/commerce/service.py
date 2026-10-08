from __future__ import annotations

from uuid import UUID

from fashx.core.context import CoreContext
from fashx.core.errors import NotFoundError
from fashx.core.event_bus import EventBus

from .entities import (
    Brand,
    Marketplace,
    MarketplaceListing,
    ProductBrand,
    Seller,
)
from .enums import (
    ListingStatus,
)
from .events import (
    BrandCreated,
    ListingCreated,
    ListingUpdated,
    MarketplaceCreated,
    ProductBrandAssigned,
    SellerCreated,
)
from .lifecycle import (
    validate_listing_transition,
)
from .repository import (
    BrandRepository,
    ListingRepository,
    MarketplaceRepository,
    ProductBrandRepository,
    SellerRepository,
)


class CommerceService:

    def __init__(
        self,
        brand_repository: BrandRepository,
        seller_repository: SellerRepository,
        marketplace_repository: MarketplaceRepository,
        product_brand_repository: ProductBrandRepository,
        listing_repository: ListingRepository,
        event_bus: EventBus,
    ) -> None:

        self.brand_repository = brand_repository
        self.seller_repository = seller_repository
        self.marketplace_repository = (
            marketplace_repository
        )
        self.product_brand_repository = (
            product_brand_repository
        )
        self.listing_repository = listing_repository
        self.event_bus = event_bus

    async def create_brand(
        self,
        *,
        context: CoreContext,
        brand: Brand,
    ) -> Brand:

        brand.validate()

        await self.brand_repository.save(brand)

        await self.event_bus.publish(
            BrandCreated(
                entity_id=brand.id,
                correlation_id=context.correlation_id,
            )
        )

        return brand

    async def create_seller(
        self,
        *,
        context: CoreContext,
        seller: Seller,
    ) -> Seller:

        seller.validate()

        await self.seller_repository.save(seller)

        await self.event_bus.publish(
            SellerCreated(
                entity_id=seller.id,
                correlation_id=context.correlation_id,
            )
        )

        return seller

    async def create_marketplace(
        self,
        *,
        context: CoreContext,
        marketplace: Marketplace,
    ) -> Marketplace:

        marketplace.validate()

        await self.marketplace_repository.save(
            marketplace
        )

        await self.event_bus.publish(
            MarketplaceCreated(
                entity_id=marketplace.id,
                correlation_id=context.correlation_id,
            )
        )

        return marketplace

    async def assign_product_brand(
        self,
        *,
        context: CoreContext,
        product_id: UUID,
        brand_id: UUID,
    ) -> ProductBrand:

        brand = await self.brand_repository.get(brand_id)

        if brand is None:
            raise NotFoundError(
                "Brand was not found.",
                {"brand_id": str(brand_id)},
            )

        relationship = ProductBrand(
            product_id=product_id,
            brand_id=brand_id,
        )

        relationship.validate()

        await self.product_brand_repository.save(
            relationship
        )

        await self.event_bus.publish(
            ProductBrandAssigned(
                entity_id=product_id,
                correlation_id=context.correlation_id,
            )
        )

        return relationship

    async def get_product_brand(
        self,
        product_id: UUID,
    ) -> ProductBrand:

        relationship = (
            await self.product_brand_repository.get(
                product_id
            )
        )

        if relationship is None:
            raise NotFoundError(
                "Product brand assignment was not found.",
                {"product_id": str(product_id)},
            )

        return relationship

    async def create_listing(
        self,
        *,
        context: CoreContext,
        listing: MarketplaceListing,
    ) -> MarketplaceListing:

        listing.validate()

        seller = await self.seller_repository.get(
            listing.seller_id
        )

        if seller is None:
            raise NotFoundError(
                "Seller was not found.",
                {"seller_id": str(listing.seller_id)},
            )

        marketplace = (
            await self.marketplace_repository.get(
                listing.marketplace_id
            )
        )

        if marketplace is None:
            raise NotFoundError(
                "Marketplace was not found.",
                {
                    "marketplace_id": str(
                        listing.marketplace_id
                    )
                },
            )

        await self.listing_repository.save(listing)

        await self.event_bus.publish(
            ListingCreated(
                entity_id=listing.id,
                correlation_id=context.correlation_id,
            )
        )

        return listing

    async def get_listing(
        self,
        listing_id: UUID,
    ) -> MarketplaceListing:

        listing = await self.listing_repository.get(
            listing_id
        )

        if listing is None:
            raise NotFoundError(
                "Marketplace listing was not found.",
                {"listing_id": str(listing_id)},
            )

        return listing

    async def list_product_listings(
        self,
        product_id: UUID,
    ) -> list[MarketplaceListing]:

        return await self.listing_repository.list_by_product(
            product_id
        )

    async def list_seller_listings(
        self,
        seller_id: UUID,
    ) -> list[MarketplaceListing]:

        return await self.listing_repository.list_by_seller(
            seller_id
        )

    async def change_listing_status(
        self,
        *,
        context: CoreContext,
        listing_id: UUID,
        target: ListingStatus,
    ) -> MarketplaceListing:

        listing = await self.get_listing(listing_id)

        validate_listing_transition(
            listing.status,
            target,
        )

        listing.status = target
        listing.touch()

        await self.listing_repository.save(listing)

        await self.event_bus.publish(
            ListingUpdated(
                entity_id=listing.id,
                correlation_id=context.correlation_id,
            )
        )

        return listing
