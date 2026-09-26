import pytest

from app.core.errors import ValidationError
from app.domain.cart.enums import CartStatus
from app.domain.cart.lifecycle import (
    validate_cart_transition,
)


def test_active_to_checkout():
    validate_cart_transition(
        CartStatus.ACTIVE,
        CartStatus.CHECKOUT,
    )


def test_checkout_to_converted():
    validate_cart_transition(
        CartStatus.CHECKOUT,
        CartStatus.CONVERTED,
    )


def test_checkout_to_active():
    validate_cart_transition(
        CartStatus.CHECKOUT,
        CartStatus.ACTIVE,
    )


def test_converted_cannot_reactivate():
    with pytest.raises(ValidationError):
        validate_cart_transition(
            CartStatus.CONVERTED,
            CartStatus.ACTIVE,
        )


def test_active_to_abandoned():
    validate_cart_transition(
        CartStatus.ACTIVE,
        CartStatus.ABANDONED,
    )


def test_abandoned_to_expired():
    validate_cart_transition(
        CartStatus.ABANDONED,
        CartStatus.EXPIRED,
    )


def test_expired_cannot_reactivate():
    with pytest.raises(ValidationError):
        validate_cart_transition(
            CartStatus.EXPIRED,
            CartStatus.ACTIVE,
        )
