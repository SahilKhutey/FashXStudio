from __future__ import annotations

from app.core.errors import ValidationError

from .enums import CartStatus

_TRANSITIONS = {
    CartStatus.ACTIVE: {
        CartStatus.CHECKOUT,
        CartStatus.ABANDONED,
        CartStatus.EXPIRED,
    },
    CartStatus.CHECKOUT: {
        CartStatus.CONVERTED,
        CartStatus.ACTIVE,
    },
    CartStatus.CONVERTED: set(),
    CartStatus.ABANDONED: {
        CartStatus.EXPIRED,
    },
    CartStatus.EXPIRED: set(),
}


def validate_cart_transition(
    current: CartStatus,
    target: CartStatus,
) -> None:
    if target not in _TRANSITIONS[current]:
        raise ValidationError(
            "Invalid cart status transition.",
            {
                "current": current.value,
                "target": target.value,
            },
        )
