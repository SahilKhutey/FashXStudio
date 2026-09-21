from enum import StrEnum


class OutfitStatus(StrEnum):
    DRAFT = "draft"
    SAVED = "saved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class OutfitVisibility(StrEnum):
    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"


class OutfitItemType(StrEnum):
    TOP = "top"
    BOTTOM = "bottom"
    DRESS = "dress"
    OUTERWEAR = "outerwear"
    FOOTWEAR = "footwear"
    ACCESSORY = "accessory"
    BAG = "bag"
    JEWELRY = "jewelry"
    HEADWEAR = "headwear"
    OTHER = "other"


class OutfitState(StrEnum):
    IDLE = "idle"
    LOADING = "loading"
    EDITING = "editing"
    READY = "ready"
    SAVED = "saved"
    PUBLISHED = "published"
    EMPTY = "empty"
    ERROR = "error"
