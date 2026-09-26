from __future__ import annotations

from enum import StrEnum


class CartStatus(StrEnum):
    ACTIVE = "active"
    CHECKOUT = "checkout"
    CONVERTED = "converted"
    ABANDONED = "abandoned"
    EXPIRED = "expired"


class CartOwnerType(StrEnum):
    ANONYMOUS = "anonymous"
    CUSTOMER = "customer"


class CartLineStatus(StrEnum):
    ACTIVE = "active"
    REMOVED = "removed"
