from enum import StrEnum


class ProductStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"


class AvailabilityStatus(StrEnum):
    AVAILABLE = "available"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    UNAVAILABLE = "unavailable"


class ProductState(StrEnum):
    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    VARIANT_SELECTION = "variant_selection"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
