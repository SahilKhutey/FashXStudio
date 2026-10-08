from enum import StrEnum


class CustomerStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    DEACTIVATED = "deactivated"


class CustomerType(StrEnum):
    INDIVIDUAL = "individual"
    BUSINESS = "business"


class AddressType(StrEnum):
    SHIPPING = "shipping"
    BILLING = "billing"
    OTHER = "other"
    HOME = "home"
    WORK = "work"


class AddressStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ConsentType(StrEnum):
    TERMS = "terms"
    PRIVACY = "privacy"
    MARKETING = "marketing"
    PERSONALIZATION = "personalization"
    ANALYTICS = "analytics"


class PreferenceScope(StrEnum):
    COMMERCE = "commerce"
    MARKETING = "marketing"
    PRIVACY = "privacy"
    UI = "ui"
