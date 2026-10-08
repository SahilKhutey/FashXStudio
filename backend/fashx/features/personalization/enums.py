from enum import StrEnum


class SignalType(StrEnum):
    VIEW = "view"
    CLICK = "click"
    LIKE = "like"
    SAVE = "save"
    SHARE = "share"
    PURCHASE = "purchase"
    ADD_TO_CART = "add_to_cart"
    SKIP = "skip"
    REJECT = "reject"
    REMOVE = "remove"


class PreferenceDomain(StrEnum):
    STYLE = "style"
    CATEGORY = "category"
    COLOR = "color"
    OCCASION = "occasion"
    SEASON = "season"
    BRAND = "brand"
    PRICE = "price"
    PRODUCT = "product"
    OUTFIT = "outfit"
    CONTENT = "content"


class PersonalizationStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


class PersonalizationState(StrEnum):
    IDLE = "idle"
    LOADING = "loading"
    LEARNING = "learning"
    READY = "ready"
    EMPTY = "empty"
    ERROR = "error"
