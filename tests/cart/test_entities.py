from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from fashx.core.errors import ValidationError
from fashx.domain.cart.entities import (
    Cart,
    CartLine,
)
from fashx.domain.cart.enums import (
    CartOwnerType,
)


def test_anonymous_cart_requires_session():
    cart = Cart(
        owner_type=CartOwnerType.ANONYMOUS
    )
    with pytest.raises(ValidationError):
        cart.validate()


def test_customer_cart_requires_customer():
    cart = Cart(
        owner_type=CartOwnerType.CUSTOMER
    )
    with pytest.raises(ValidationError):
        cart.validate()


def test_cart_line_valid():
    line = CartLine(
        cart_id=uuid4(),
        product_id=uuid4(),
        quantity=2,
        unit_price=Decimal("1000"),
        currency="INR",
    )
    line.validate()
    assert line.subtotal == Decimal("2000")


def test_cart_line_quantity_validation():
    line = CartLine(
        cart_id=uuid4(),
        product_id=uuid4(),
        quantity=0,
        unit_price=Decimal("1000"),
        currency="INR",
    )
    with pytest.raises(ValidationError):
        line.validate()

    line.quantity = 2
    line.validate()
    line.update_quantity(3)
    assert line.quantity == 3

    with pytest.raises(ValidationError):
        line.update_quantity(0)


def test_cart_line_negative_price():
    line = CartLine(
        cart_id=uuid4(),
        product_id=uuid4(),
        quantity=1,
        unit_price=Decimal("-10"),
        currency="INR",
    )
    with pytest.raises(ValidationError):
        line.validate()


def test_cart_line_currency_validation():
    line = CartLine(
        cart_id=uuid4(),
        product_id=uuid4(),
        quantity=1,
        unit_price=Decimal("100"),
        currency="TOOLONG",
    )
    with pytest.raises(ValidationError):
        line.validate()


def test_cart_expiration():
    now = datetime.now(UTC)
    cart = Cart(
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="session-1",
        expires_at=now - timedelta(hours=1),
    )
    assert cart.is_expired(now) is True

    cart.expires_at = now + timedelta(hours=1)
    assert cart.is_expired(now) is False


def test_cart_version_and_touch():
    cart = Cart(
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="session-1",
    )
    cart.validate()
    v1 = cart.version
    cart.touch()
    assert cart.version == v1 + 1
