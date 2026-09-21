from enum import StrEnum


class SearchResultType(StrEnum):
    PRODUCT = "product"
    OUTFIT = "outfit"
    CONTENT = "content"
    COLLECTION = "collection"
    TREND = "trend"
    CATEGORY = "category"
    STYLE = "style"
    BRAND = "brand"


class SearchMode(StrEnum):
    GLOBAL = "global"
    PRODUCTS = "products"
    OUTFITS = "outfits"
    CONTENT = "content"
    TRENDS = "trends"


class SortOption(StrEnum):
    RELEVANCE = "relevance"
    POPULARITY = "popularity"
    TRENDING = "trending"
    NEWEST = "newest"
    PRICE_LOW_TO_HIGH = "price_low_to_high"
    PRICE_HIGH_TO_LOW = "price_high_to_low"


class SearchStatus(StrEnum):
    IDLE = "idle"
    SUGGESTING = "suggesting"
    SEARCHING = "searching"
    READY = "ready"
    EMPTY = "empty"
    ERROR = "error"
