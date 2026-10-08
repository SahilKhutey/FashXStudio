from fashx.core.errors import ConflictError

from .enums import OrderStatus

TRANSITIONS = {
    OrderStatus.PENDING: {
        OrderStatus.CONFIRMED,
        OrderStatus.CANCELLED,
        OrderStatus.FAILED,
    },
    OrderStatus.CONFIRMED: {
        OrderStatus.PROCESSING,
        OrderStatus.CANCELLED,
    },
    OrderStatus.PROCESSING: {
        OrderStatus.FULFILLED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.FULFILLED: {
        OrderStatus.COMPLETED,
    },
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
    OrderStatus.FAILED: set(),
}


def validate_transition(
    current: OrderStatus,
    target: OrderStatus,
) -> None:
    allowed = TRANSITIONS.get(
        current,
        set(),
    )

    if target not in allowed:
        raise ConflictError(
            f"Invalid order transition: {current} -> {target}"
        )


validate_order_transition = validate_transition
