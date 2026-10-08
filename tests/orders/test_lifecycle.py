import pytest

from app.core.errors import ConflictError
from fashx.domain.order.enums import OrderStatus
from fashx.domain.order.lifecycle import (
    validate_transition,
)


def test_pending_to_confirmed():
    validate_transition(
        OrderStatus.PENDING,
        OrderStatus.CONFIRMED,
    )


def test_completed_is_terminal():
    with pytest.raises(ConflictError):
        validate_transition(
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
        )


def test_valid_order_transitions():
    # PENDING -> CANCELLED, FAILED
    validate_transition(OrderStatus.PENDING, OrderStatus.CANCELLED)
    validate_transition(OrderStatus.PENDING, OrderStatus.FAILED)

    # CONFIRMED -> PROCESSING, CANCELLED
    validate_transition(OrderStatus.CONFIRMED, OrderStatus.PROCESSING)
    validate_transition(OrderStatus.CONFIRMED, OrderStatus.CANCELLED)

    # PROCESSING -> FULFILLED, CANCELLED
    validate_transition(OrderStatus.PROCESSING, OrderStatus.FULFILLED)
    validate_transition(OrderStatus.PROCESSING, OrderStatus.CANCELLED)

    # FULFILLED -> COMPLETED
    validate_transition(OrderStatus.FULFILLED, OrderStatus.COMPLETED)


def test_terminal_order_states():
    with pytest.raises(ConflictError):
        validate_transition(OrderStatus.CANCELLED, OrderStatus.PENDING)

    with pytest.raises(ConflictError):
        validate_transition(OrderStatus.FAILED, OrderStatus.CONFIRMED)

    with pytest.raises(ConflictError):
        validate_transition(OrderStatus.COMPLETED, OrderStatus.PROCESSING)
