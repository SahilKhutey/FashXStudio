import pytest

from app.core.errors import ValidationError
from app.domain.commerce.enums import (
    BrandStatus,
    ListingStatus,
    MarketplaceStatus,
    SellerStatus,
)
from app.domain.commerce.lifecycle import (
    validate_brand_transition,
    validate_listing_transition,
    validate_marketplace_transition,
    validate_seller_transition,
)


def test_brand_activation():

    validate_brand_transition(
        BrandStatus.DRAFT,
        BrandStatus.ACTIVE,
    )


def test_seller_activation():

    validate_seller_transition(
        SellerStatus.PENDING,
        SellerStatus.ACTIVE,
    )


def test_marketplace_activation():

    validate_marketplace_transition(
        MarketplaceStatus.DRAFT,
        MarketplaceStatus.ACTIVE,
    )


def test_listing_activation():

    validate_listing_transition(
        ListingStatus.DRAFT,
        ListingStatus.ACTIVE,
    )


def test_ended_listing_cannot_reactivate():

    with pytest.raises(ValidationError):
        validate_listing_transition(
            ListingStatus.ENDED,
            ListingStatus.ACTIVE,
        )


def test_closed_seller_cannot_reactivate():

    with pytest.raises(ValidationError):
        validate_seller_transition(
            SellerStatus.CLOSED,
            SellerStatus.ACTIVE,
        )
