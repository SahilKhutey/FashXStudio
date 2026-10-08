import pytest

from app.core.errors import ValidationError
from app.core.ids import new_id
from fashx.domain.commerce.entities import (
    Brand,
    Marketplace,
    MarketplaceListing,
    Seller,
)
from fashx.domain.commerce.enums import (
    SellerType,
)


def test_brand_validates():

    brand = Brand(
        name="FashX",
        slug="fashx",
    )

    brand.validate()


def test_brand_requires_name():

    brand = Brand(
        name="",
        slug="fashx",
    )

    with pytest.raises(ValidationError):
        brand.validate()


def test_seller_validates():

    seller = Seller(
        name="Example Seller",
        slug="example-seller",
        seller_type=SellerType.RETAILER,
    )

    seller.validate()


def test_marketplace_validates():

    marketplace = Marketplace(
        name="Example Market",
        slug="example-market",
    )

    marketplace.validate()


def test_listing_requires_seller():

    listing = MarketplaceListing(
        product_id=new_id(),
        marketplace_id=new_id(),
    )

    with pytest.raises(ValidationError):
        listing.validate()


def test_listing_requires_marketplace():

    listing = MarketplaceListing(
        product_id=new_id(),
        seller_id=new_id(),
    )

    with pytest.raises(ValidationError):
        listing.validate()
