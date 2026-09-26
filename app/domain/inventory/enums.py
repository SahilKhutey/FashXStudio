from __future__ import annotations

from enum import StrEnum


class InventoryStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class AvailabilityStatus(StrEnum):
    AVAILABLE = "available"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    UNAVAILABLE = "unavailable"


class StockAdjustmentType(StrEnum):
    RECEIVE = "receive"
    ADD = "add"
    REMOVE = "remove"
    DAMAGE = "damage"
    LOSS = "loss"
    CORRECTION = "correction"


class StockLocationType(StrEnum):
    WAREHOUSE = "warehouse"
    STORE = "store"
    DISTRIBUTION_CENTER = "distribution_center"
    OTHER = "other"
