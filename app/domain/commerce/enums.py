from __future__ import annotations

from enum import StrEnum


class BrandStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class SellerStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class MarketplaceStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class ListingStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


class SellerType(StrEnum):
    BRAND = "brand"
    RETAILER = "retailer"
    DISTRIBUTOR = "distributor"
    INDIVIDUAL = "individual"
    MARKETPLACE = "marketplace"


class ListingTarget(StrEnum):
    PRODUCT = "product"
    VARIANT = "variant"
