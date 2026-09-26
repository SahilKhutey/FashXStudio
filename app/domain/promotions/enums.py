from __future__ import annotations

from enum import StrEnum


class PromotionStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class OfferStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class DiscountType(StrEnum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class PromotionScope(StrEnum):
    PRODUCT = "product"
    VARIANT = "variant"
    LISTING = "listing"
    SELLER = "seller"
    MARKETPLACE = "marketplace"


class EligibilityType(StrEnum):
    EVERYONE = "everyone"
    MINIMUM_VALUE = "minimum_value"
    CUSTOMER = "customer"
    REGION = "region"
