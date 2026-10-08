from fashx.core.errors import ValidationError

from .enums import (
    CancellationStatus,
    RefundStatus,
    ReturnStatus,
)

CANCELLATION_TRANSITIONS = {
    CancellationStatus.REQUESTED: {
        CancellationStatus.APPROVED,
        CancellationStatus.REJECTED,
    },
    CancellationStatus.APPROVED: {
        CancellationStatus.COMPLETED,
    },
    CancellationStatus.REJECTED: set(),
    CancellationStatus.COMPLETED: set(),
}


RETURN_TRANSITIONS = {
    ReturnStatus.REQUESTED: {
        ReturnStatus.APPROVED,
        ReturnStatus.REJECTED,
        ReturnStatus.CANCELLED,
    },
    ReturnStatus.APPROVED: {
        ReturnStatus.PICKUP_PENDING,
        ReturnStatus.CANCELLED,
    },
    ReturnStatus.PICKUP_PENDING: {
        ReturnStatus.IN_TRANSIT,
        ReturnStatus.CANCELLED,
    },
    ReturnStatus.IN_TRANSIT: {
        ReturnStatus.RECEIVED,
    },
    ReturnStatus.RECEIVED: {
        ReturnStatus.INSPECTION,
    },
    ReturnStatus.INSPECTION: {
        ReturnStatus.ACCEPTED,
        ReturnStatus.REJECTED,
    },
    ReturnStatus.ACCEPTED: {
        ReturnStatus.COMPLETED,
    },
    ReturnStatus.REJECTED: set(),
    ReturnStatus.COMPLETED: set(),
    ReturnStatus.CANCELLED: set(),
}


REFUND_TRANSITIONS = {
    RefundStatus.REQUESTED: {
        RefundStatus.APPROVED,
        RefundStatus.CANCELLED,
    },
    RefundStatus.APPROVED: {
        RefundStatus.PROCESSING,
    },
    RefundStatus.PROCESSING: {
        RefundStatus.COMPLETED,
        RefundStatus.FAILED,
    },
    RefundStatus.FAILED: {
        RefundStatus.PROCESSING,
        RefundStatus.CANCELLED,
    },
    RefundStatus.COMPLETED: set(),
    RefundStatus.CANCELLED: set(),
}


def validate_transition(
    current,
    target,
    transitions: dict,
    entity_name: str,
) -> None:
    if target not in transitions[current]:
        raise ValidationError(
            f"Invalid {entity_name} transition.",
            {
                "current": current.value,
                "target": target.value,
            },
        )
