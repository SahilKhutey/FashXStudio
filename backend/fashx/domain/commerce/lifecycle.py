from __future__ import annotations

from app.core.errors import ValidationError

from .enums import (
    BrandStatus,
    ListingStatus,
    MarketplaceStatus,
    SellerStatus,
)

_BRAND_TRANSITIONS = {
    BrandStatus.DRAFT: {
        BrandStatus.ACTIVE,
        BrandStatus.ARCHIVED,
    },
    BrandStatus.ACTIVE: {
        BrandStatus.SUSPENDED,
        BrandStatus.ARCHIVED,
    },
    BrandStatus.SUSPENDED: {
        BrandStatus.ACTIVE,
        BrandStatus.ARCHIVED,
    },
    BrandStatus.ARCHIVED: set(),
}


_SELLER_TRANSITIONS = {
    SellerStatus.PENDING: {
        SellerStatus.ACTIVE,
        SellerStatus.CLOSED,
    },
    SellerStatus.ACTIVE: {
        SellerStatus.SUSPENDED,
        SellerStatus.CLOSED,
    },
    SellerStatus.SUSPENDED: {
        SellerStatus.ACTIVE,
        SellerStatus.CLOSED,
    },
    SellerStatus.CLOSED: set(),
}


_MARKETPLACE_TRANSITIONS = {
    MarketplaceStatus.DRAFT: {
        MarketplaceStatus.ACTIVE,
        MarketplaceStatus.CLOSED,
    },
    MarketplaceStatus.ACTIVE: {
        MarketplaceStatus.SUSPENDED,
        MarketplaceStatus.CLOSED,
    },
    MarketplaceStatus.SUSPENDED: {
        MarketplaceStatus.ACTIVE,
        MarketplaceStatus.CLOSED,
    },
    MarketplaceStatus.CLOSED: set(),
}


_LISTING_TRANSITIONS = {
    ListingStatus.DRAFT: {
        ListingStatus.ACTIVE,
        ListingStatus.ENDED,
    },
    ListingStatus.ACTIVE: {
        ListingStatus.PAUSED,
        ListingStatus.ENDED,
    },
    ListingStatus.PAUSED: {
        ListingStatus.ACTIVE,
        ListingStatus.ENDED,
    },
    ListingStatus.ENDED: set(),
}


def _validate(
    current,
    target,
    transitions,
    entity_name: str,
) -> None:

    if target not in transitions[current]:
        raise ValidationError(
            f"Invalid {entity_name} status transition.",
            {
                "current": current.value,
                "target": target.value,
            },
        )


def validate_brand_transition(
    current: BrandStatus,
    target: BrandStatus,
) -> None:

    _validate(
        current,
        target,
        _BRAND_TRANSITIONS,
        "brand",
    )


def validate_seller_transition(
    current: SellerStatus,
    target: SellerStatus,
) -> None:

    _validate(
        current,
        target,
        _SELLER_TRANSITIONS,
        "seller",
    )


def validate_marketplace_transition(
    current: MarketplaceStatus,
    target: MarketplaceStatus,
) -> None:

    _validate(
        current,
        target,
        _MARKETPLACE_TRANSITIONS,
        "marketplace",
    )


def validate_listing_transition(
    current: ListingStatus,
    target: ListingStatus,
) -> None:

    _validate(
        current,
        target,
        _LISTING_TRANSITIONS,
        "listing",
    )
