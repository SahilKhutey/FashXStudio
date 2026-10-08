from __future__ import annotations

from fashx.core.errors import ValidationError

from .enums import PaymentStatus

_PAYMENT_TRANSITIONS = {
    PaymentStatus.CREATED: {
        PaymentStatus.REQUIRES_ACTION,
        PaymentStatus.AUTHORIZED,
        PaymentStatus.FAILED,
        PaymentStatus.CANCELLED,
    },
    PaymentStatus.REQUIRES_ACTION: {
        PaymentStatus.AUTHORIZED,
        PaymentStatus.FAILED,
        PaymentStatus.CANCELLED,
    },
    PaymentStatus.AUTHORIZED: {
        PaymentStatus.CAPTURED,
        PaymentStatus.CANCELLED,
    },
    PaymentStatus.CAPTURED: set(),
    PaymentStatus.FAILED: set(),
    PaymentStatus.CANCELLED: set(),
}


def validate_payment_transition(
    current: PaymentStatus,
    target: PaymentStatus,
) -> None:
    if target not in _PAYMENT_TRANSITIONS[current]:
        raise ValidationError(
            "Invalid payment status transition.",
            {
                "current": current.value,
                "target": target.value,
            },
        )
