from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.errors import ValidationError
from fashx.domain.payments.entities import (
    Payment,
    PaymentTransaction,
)
from fashx.domain.payments.enums import (
    PaymentMethodType,
    PaymentStatus,
    TransactionType,
)


def test_payment_requires_order() -> None:
    payment = Payment(
        amount=Decimal("100"),
    )
    with pytest.raises(ValidationError, match="Payment requires order ID"):
        payment.validate()


def test_payment_requires_positive_amount() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount=Decimal("0"),
    )
    with pytest.raises(
        ValidationError, match="Payment amount must be greater than zero"
    ):
        payment.validate()


def test_valid_payment() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount=Decimal("999"),
        currency="INR",
        method=PaymentMethodType.UPI,
    )
    payment.validate()
    assert payment.status == PaymentStatus.CREATED


def test_payment_validation_errors() -> None:
    order_id = uuid4()

    # Invalid currency length
    p1 = Payment(order_id=order_id, amount=Decimal("10"), currency="US")
    with pytest.raises(
        ValidationError, match="Currency must be a 3-character code"
    ):
        p1.validate()

    # Empty provider
    p2 = Payment(order_id=order_id, amount=Decimal("10"), provider="   ")
    with pytest.raises(ValidationError, match="Payment provider is required"):
        p2.validate()

    # Invalid version
    p3 = Payment(order_id=order_id, amount=Decimal("10"), version=0)
    with pytest.raises(
        ValidationError, match="Payment version must be positive"
    ):
        p3.validate()


def test_payment_touch() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount=Decimal("500"),
    )
    orig_version = payment.version
    payment.touch()
    assert payment.version == orig_version + 1


def test_payment_transaction_validation() -> None:
    # Missing payment ID
    t1 = PaymentTransaction(amount=Decimal("100"))
    with pytest.raises(
        ValidationError, match="Transaction requires payment ID"
    ):
        t1.validate()

    # Zero or negative amount
    t2 = PaymentTransaction(payment_id=uuid4(), amount=Decimal("0"))
    with pytest.raises(
        ValidationError, match="Transaction amount must be positive"
    ):
        t2.validate()

    # Invalid currency length
    t3 = PaymentTransaction(
        payment_id=uuid4(), amount=Decimal("100"), currency="IN"
    )
    with pytest.raises(ValidationError, match="Currency must be 3 characters"):
        t3.validate()

    # Valid transaction
    valid_tx = PaymentTransaction(
        payment_id=uuid4(),
        transaction_type=TransactionType.AUTHORIZATION,
        amount=Decimal("100"),
        currency="INR",
    )
    valid_tx.validate()
