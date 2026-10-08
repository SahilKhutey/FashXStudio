from fashx.core.errors import ConflictError

from .enums import CheckoutStatus

TRANSITIONS = {
    CheckoutStatus.OPEN: {
        CheckoutStatus.VALIDATING,
        CheckoutStatus.CANCELLED,
        CheckoutStatus.EXPIRED,
    },
    CheckoutStatus.VALIDATING: {
        CheckoutStatus.READY,
        CheckoutStatus.OPEN,
        CheckoutStatus.EXPIRED,
    },
    CheckoutStatus.READY: {
        CheckoutStatus.PAYMENT_PENDING,
        CheckoutStatus.OPEN,
        CheckoutStatus.EXPIRED,
    },
    CheckoutStatus.PAYMENT_PENDING: {
        CheckoutStatus.COMPLETED,
        CheckoutStatus.READY,
        CheckoutStatus.CANCELLED,
    },
    CheckoutStatus.COMPLETED: set(),
    CheckoutStatus.EXPIRED: set(),
    CheckoutStatus.CANCELLED: set(),
}


def validate_transition(
    current: CheckoutStatus,
    target: CheckoutStatus,
) -> None:
    if target not in TRANSITIONS.get(
        current,
        set(),
    ):
        raise ConflictError(
            f"Invalid checkout transition: {current} -> {target}"
        )


validate_checkout_transition = validate_transition
