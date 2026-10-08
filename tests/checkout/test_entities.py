from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.errors import ValidationError
from fashx.domain.checkout.entities import (
    CheckoutSession,
)


def test_checkout_requires_cart():
    checkout = CheckoutSession()
    with pytest.raises(ValidationError):
        checkout.validate()


def test_checkout_valid():
    checkout = CheckoutSession(
        cart_id=uuid4()
    )
    checkout.validate()


def test_checkout_validation_errors():
    # Invalid currency length
    with pytest.raises(ValidationError, match="Currency must be 3 characters"):
        CheckoutSession(cart_id=uuid4(), currency="TOOLONG").validate()

    # Invalid version
    with pytest.raises(ValidationError, match="Version must be positive"):
        CheckoutSession(cart_id=uuid4(), version=0).validate()


def test_checkout_expiration_and_touch():
    now = datetime.now(UTC)
    checkout = CheckoutSession(
        cart_id=uuid4(),
        expires_at=now + timedelta(hours=1),
    )
    assert checkout.is_expired(now) is False
    assert checkout.is_expired(now + timedelta(hours=2)) is True

    no_expiry_checkout = CheckoutSession(cart_id=uuid4())
    assert no_expiry_checkout.is_expired(now) is False

    orig_version = checkout.version
    checkout.touch()
    assert checkout.version == orig_version + 1
