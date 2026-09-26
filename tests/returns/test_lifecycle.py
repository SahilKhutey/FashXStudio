import pytest

from app.core.errors import ValidationError
from app.domain.returns.enums import (
    CancellationStatus,
    RefundStatus,
    ReturnStatus,
)
from app.domain.returns.lifecycle import (
    CANCELLATION_TRANSITIONS,
    REFUND_TRANSITIONS,
    RETURN_TRANSITIONS,
    validate_transition,
)


def test_return_happy_path():
    flow = [
        (ReturnStatus.REQUESTED, ReturnStatus.APPROVED),
        (ReturnStatus.APPROVED, ReturnStatus.PICKUP_PENDING),
        (ReturnStatus.PICKUP_PENDING, ReturnStatus.IN_TRANSIT),
        (ReturnStatus.IN_TRANSIT, ReturnStatus.RECEIVED),
        (ReturnStatus.RECEIVED, ReturnStatus.INSPECTION),
        (ReturnStatus.INSPECTION, ReturnStatus.ACCEPTED),
        (ReturnStatus.ACCEPTED, ReturnStatus.COMPLETED),
    ]
    for current, target in flow:
        validate_transition(current, target, RETURN_TRANSITIONS, "return")


def test_return_rejection_and_cancellation():
    validate_transition(
        ReturnStatus.INSPECTION, ReturnStatus.REJECTED, RETURN_TRANSITIONS, "return"
    )
    validate_transition(
        ReturnStatus.REQUESTED, ReturnStatus.CANCELLED, RETURN_TRANSITIONS, "return"
    )
    validate_transition(
        ReturnStatus.APPROVED, ReturnStatus.CANCELLED, RETURN_TRANSITIONS, "return"
    )
    validate_transition(
        ReturnStatus.PICKUP_PENDING, ReturnStatus.CANCELLED, RETURN_TRANSITIONS, "return"
    )


def test_completed_return_terminal():
    with pytest.raises(ValidationError, match="Invalid return transition"):
        validate_transition(
            ReturnStatus.COMPLETED,
            ReturnStatus.REJECTED,
            RETURN_TRANSITIONS,
            "return",
        )

    with pytest.raises(ValidationError, match="Invalid return transition"):
        validate_transition(
            ReturnStatus.REJECTED,
            ReturnStatus.ACCEPTED,
            RETURN_TRANSITIONS,
            "return",
        )


def test_cancellation_lifecycle():
    validate_transition(
        CancellationStatus.REQUESTED,
        CancellationStatus.APPROVED,
        CANCELLATION_TRANSITIONS,
        "cancellation",
    )
    validate_transition(
        CancellationStatus.APPROVED,
        CancellationStatus.COMPLETED,
        CANCELLATION_TRANSITIONS,
        "cancellation",
    )
    validate_transition(
        CancellationStatus.REQUESTED,
        CancellationStatus.REJECTED,
        CANCELLATION_TRANSITIONS,
        "cancellation",
    )

    with pytest.raises(ValidationError, match="Invalid cancellation transition"):
        validate_transition(
            CancellationStatus.COMPLETED,
            CancellationStatus.REQUESTED,
            CANCELLATION_TRANSITIONS,
            "cancellation",
        )


def test_refund_lifecycle_and_retry():
    validate_transition(
        RefundStatus.REQUESTED,
        RefundStatus.APPROVED,
        REFUND_TRANSITIONS,
        "refund",
    )
    validate_transition(
        RefundStatus.APPROVED,
        RefundStatus.PROCESSING,
        REFUND_TRANSITIONS,
        "refund",
    )
    validate_transition(
        RefundStatus.PROCESSING,
        RefundStatus.COMPLETED,
        REFUND_TRANSITIONS,
        "refund",
    )
    validate_transition(
        RefundStatus.PROCESSING,
        RefundStatus.FAILED,
        REFUND_TRANSITIONS,
        "refund",
    )
    # Retry from FAILED
    validate_transition(
        RefundStatus.FAILED,
        RefundStatus.PROCESSING,
        REFUND_TRANSITIONS,
        "refund",
    )

    with pytest.raises(ValidationError, match="Invalid refund transition"):
        validate_transition(
            RefundStatus.COMPLETED,
            RefundStatus.PROCESSING,
            REFUND_TRANSITIONS,
            "refund",
        )
