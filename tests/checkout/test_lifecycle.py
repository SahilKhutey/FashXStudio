import pytest

from app.core.errors import ConflictError
from app.domain.checkout.enums import CheckoutStatus
from app.domain.checkout.lifecycle import (
    validate_transition,
)


def test_open_to_validating():
    validate_transition(CheckoutStatus.OPEN, CheckoutStatus.VALIDATING)


def test_validating_to_ready():
    validate_transition(CheckoutStatus.VALIDATING, CheckoutStatus.READY)


def test_ready_to_payment_pending():
    validate_transition(CheckoutStatus.READY, CheckoutStatus.PAYMENT_PENDING)


def test_payment_pending_to_completed():
    validate_transition(CheckoutStatus.PAYMENT_PENDING, CheckoutStatus.COMPLETED)


def test_terminal_states():
    with pytest.raises(ConflictError):
        validate_transition(CheckoutStatus.COMPLETED, CheckoutStatus.OPEN)

    with pytest.raises(ConflictError):
        validate_transition(CheckoutStatus.EXPIRED, CheckoutStatus.VALIDATING)

    with pytest.raises(ConflictError):
        validate_transition(CheckoutStatus.CANCELLED, CheckoutStatus.READY)


def test_invalid_transitions():
    with pytest.raises(ConflictError):
        validate_transition(CheckoutStatus.OPEN, CheckoutStatus.COMPLETED)

    with pytest.raises(ConflictError):
        validate_transition(CheckoutStatus.VALIDATING, CheckoutStatus.COMPLETED)
