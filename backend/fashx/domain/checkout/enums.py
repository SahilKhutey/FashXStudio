from enum import StrEnum


class CheckoutStatus(StrEnum):
    OPEN = "open"
    VALIDATING = "validating"
    READY = "ready"
    PAYMENT_PENDING = "payment_pending"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    CREATED = "open"
