from enum import StrEnum


class ContentType(StrEnum):
    POST = "post"
    ARTICLE = "article"
    LOOKBOOK = "lookbook"
    STYLE_GUIDE = "style_guide"
    TREND_REPORT = "trend_report"
    OUTFIT_STORY = "outfit_story"
    PRODUCT_STORY = "product_story"
    COLLECTION_STORY = "collection_story"
    FASHION_TIP = "fashion_tip"


class ContentStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ContentVisibility(StrEnum):
    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"


class ContentState(StrEnum):
    IDLE = "idle"
    LOADING = "loading"
    EDITING = "editing"
    READY = "ready"
    PUBLISHED = "published"
    EMPTY = "empty"
    ERROR = "error"
