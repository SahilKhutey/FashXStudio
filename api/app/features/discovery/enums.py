from enum import StrEnum


class DiscoveryItemType(StrEnum):
    PRODUCT = "product"
    OUTFIT = "outfit"
    CONTENT = "content"
    COLLECTION = "collection"
    TREND = "trend"


class DiscoverySurface(StrEnum):
    FOR_YOU = "for_you"
    CATEGORIES = "categories"
    TRENDING = "trending"
    COLLECTIONS = "collections"


class DiscoveryStatus(StrEnum):
    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    EMPTY = "empty"
    ERROR = "error"
