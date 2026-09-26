from __future__ import annotations

from enum import StrEnum


class CheckoutStatus(StrEnum):
    CREATED = "created"
    VALIDATED = "validated"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class OrderStatus(StrEnum):
    PENDING_PAYMENT = "pending_payment"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class OrderLineStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
