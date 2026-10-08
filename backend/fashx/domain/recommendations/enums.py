from enum import StrEnum


class RecommendationSource(StrEnum):
    PERSONALIZED = "personalized"
    CATEGORY = "category"
    BRAND = "brand"
    STYLE = "style"
    POPULAR = "popular"
    RECENT = "recent"
    TRENDING = "trending"
    SIMILAR = "similar"
    CURATED = "curated"


class RecommendationReason(StrEnum):
    STYLE_MATCH = "style_match"
    CATEGORY_MATCH = "category_match"
    BRAND_MATCH = "brand_match"
    COLOR_MATCH = "color_match"
    MATERIAL_MATCH = "material_match"
    OCCASION_MATCH = "occasion_match"
    PRICE_MATCH = "price_match"
    REGION_MATCH = "region_match"
    SIMILAR_ITEM = "similar_item"


class RecommendationStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    DISABLED = "disabled"
