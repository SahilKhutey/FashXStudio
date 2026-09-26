from __future__ import annotations

from enum import StrEnum


class Currency(StrEnum):
    INR = "INR"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


class PriceStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class PriceType(StrEnum):
    BASE = "base"
    SALE = "sale"
    REGIONAL = "regional"


class RuleStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class DiscountType(StrEnum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class RuleScope(StrEnum):
    PRODUCT = "product"
    VARIANT = "variant"
    LISTING = "listing"
    CART = "cart"
    CUSTOMER = "customer"
    REGION = "region"
