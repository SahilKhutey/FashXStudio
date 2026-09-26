import pytest

from app.core.context import CoreContext
from app.core.event_bus import EventBus
from app.core.ids import new_id
from app.domain.commerce.entities import (
    Brand,
    Marketplace,
    MarketplaceListing,
    Seller,
)
from app.domain.commerce.enums import (
    ListingStatus,
)
from app.domain.commerce.service import CommerceService
from app.repositories.commerce.memory import (
    InMemoryBrandRepository,
    InMemoryListingRepository,
    InMemoryMarketplaceRepository,
    InMemoryProductBrandRepository,
    InMemorySellerRepository,
)


@pytest.fixture
def service():

    return CommerceService(
        brand_repository=InMemoryBrandRepository(),
        seller_repository=InMemorySellerRepository(),
        marketplace_repository=(
            InMemoryMarketplaceRepository()
        ),
        product_brand_repository=(
            InMemoryProductBrandRepository()
        ),
        listing_repository=(
            InMemoryListingRepository()
        ),
        event_bus=EventBus(),
    )


@pytest.mark.asyncio
async def test_create_brand(service):

    brand = await service.create_brand(
        context=CoreContext.create(),
        brand=Brand(
            name="FashX",
            slug="fashx",
        ),
    )

    assert brand.name == "FashX"


@pytest.mark.asyncio
async def test_create_seller(service):

    seller = await service.create_seller(
        context=CoreContext.create(),
        seller=Seller(
            name="Seller A",
            slug="seller-a",
        ),
    )

    assert seller.slug == "seller-a"


@pytest.mark.asyncio
async def test_create_marketplace(service):

    marketplace = await service.create_marketplace(
        context=CoreContext.create(),
        marketplace=Marketplace(
            name="Market A",
            slug="market-a",
        ),
    )

    assert marketplace.slug == "market-a"


@pytest.mark.asyncio
async def test_assign_product_brand(service):

    brand = await service.create_brand(
        context=CoreContext.create(),
        brand=Brand(
            name="FashX",
            slug="fashx",
        ),
    )

    product_id = new_id()

    relationship = (
        await service.assign_product_brand(
            context=CoreContext.create(),
            product_id=product_id,
            brand_id=brand.id,
        )
    )

    assert relationship.product_id == product_id
    assert relationship.brand_id == brand.id


@pytest.mark.asyncio
async def test_create_listing(service):

    seller = await service.create_seller(
        context=CoreContext.create(),
        seller=Seller(
            name="Seller A",
            slug="seller-a",
        ),
    )

    marketplace = await service.create_marketplace(
        context=CoreContext.create(),
        marketplace=Marketplace(
            name="Market A",
            slug="market-a",
        ),
    )

    listing = await service.create_listing(
        context=CoreContext.create(),
        listing=MarketplaceListing(
            product_id=new_id(),
            seller_id=seller.id,
            marketplace_id=marketplace.id,
        ),
    )

    assert listing.seller_id == seller.id
    assert listing.marketplace_id == marketplace.id


@pytest.mark.asyncio
async def test_listing_status_change(service):

    seller = await service.create_seller(
        context=CoreContext.create(),
        seller=Seller(
            name="Seller A",
            slug="seller-a",
        ),
    )

    marketplace = await service.create_marketplace(
        context=CoreContext.create(),
        marketplace=Marketplace(
            name="Market A",
            slug="market-a",
        ),
    )

    listing = await service.create_listing(
        context=CoreContext.create(),
        listing=MarketplaceListing(
            product_id=new_id(),
            seller_id=seller.id,
            marketplace_id=marketplace.id,
        ),
    )

    result = await service.change_listing_status(
        context=CoreContext.create(),
        listing_id=listing.id,
        target=ListingStatus.ACTIVE,
    )

    assert result.status == ListingStatus.ACTIVE
