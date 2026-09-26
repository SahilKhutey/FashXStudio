from enum import StrEnum


class TrendType(StrEnum):
    STYLE = "style"
    COLOR = "color"
    MATERIAL = "material"
    CATEGORY = "category"
    PRODUCT = "product"
    BRAND = "brand"
    OCCASION = "occasion"


class TrendDirection(StrEnum):
    RISING = "rising"
    STABLE = "stable"
    DECLINING = "declining"


class TrendStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class TrendSource(StrEnum):
    SEARCH = "search"
    MARKETPLACE = "marketplace"
    SOCIAL = "social"
    EDITORIAL = "editorial"
    INTERNAL_BEHAVIOR = "internal_behavior"
    SALES = "sales"
    CATALOG = "catalog"
    CURATED = "curated"
    IMPORTED = "imported"


class SignalType(StrEnum):
    SEARCH_VOLUME = "search_volume"
    PRODUCT_VIEWS = "product_views"
    CLICKS = "clicks"
    ADD_TO_CART = "add_to_cart"
    PURCHASES = "purchases"
    MENTIONS = "mentions"
    LISTING_COUNT = "listing_count"
    ENGAGEMENT = "engagement"
