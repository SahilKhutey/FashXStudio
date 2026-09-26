from __future__ import annotations

from app.core.errors import ValidationError

from .enums import OrderStatus

_ORDER_TRANSITIONS = {
    OrderStatus.PENDING_PAYMENT: {
        OrderStatus.CONFIRMED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.CONFIRMED: {
        OrderStatus.PROCESSING,
        OrderStatus.CANCELLED,
    },
    OrderStatus.PROCESSING: {
        OrderStatus.SHIPPED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.SHIPPED: {
        OrderStatus.DELIVERED,
    },
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
    OrderStatus.REFUNDED: set(),
}


def validate_order_transition(
    current: OrderStatus,
    target: OrderStatus,
) -> None:
    if target not in _ORDER_TRANSITIONS[current]:
        raise ValidationError(
            "Invalid order status transition.",
            {
                "current": current.value,
                "target": target.value,
            },
        )
