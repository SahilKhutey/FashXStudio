from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from fashx.core.errors import ValidationError
from fashx.domain.pricing.entities import Price
from fashx.domain.pricing.enums import PriceStatus, PriceType


def test_price_requires_target():
    price = Price(amount=Decimal("100"))
    with pytest.raises(ValidationError, match="Price requires product, variant, or listing"):
        price.validate()


def test_negative_price_rejected():
    price = Price(
        product_id=uuid4(),
        amount=Decimal("-1"),
    )
    with pytest.raises(ValidationError, match="Price amount cannot be negative"):
        price.validate()


def test_invalid_currency_rejected():
    price = Price(
        product_id=uuid4(),
        amount=Decimal("100"),
        currency="TOOLONG",
    )
    with pytest.raises(ValidationError, match="Currency must be a 3-character code"):
        price.validate()


def test_invalid_validity_window():
    now = datetime.now(UTC)
    price = Price(
        product_id=uuid4(),
        amount=Decimal("100"),
        valid_from=now,
        valid_until=now - timedelta(days=1),
    )
    with pytest.raises(ValidationError, match="Price validity window is invalid"):
        price.validate()


def test_invalid_version():
    price = Price(
        product_id=uuid4(),
        amount=Decimal("100"),
        version=0,
    )
    with pytest.raises(ValidationError, match="Price version must be positive"):
        price.validate()


def test_valid_price():
    price = Price(
        product_id=uuid4(),
        amount=Decimal("999.99"),
        price_type=PriceType.BASE,
        status=PriceStatus.ACTIVE,
    )
    price.validate()
    assert price.version == 1
    price.touch()
    assert price.version == 2


def test_price_is_valid_at():
    now = datetime.now(UTC)
    price = Price(
        product_id=uuid4(),
        amount=Decimal("100"),
        status=PriceStatus.ACTIVE,
        valid_from=now - timedelta(days=1),
        valid_until=now + timedelta(days=1),
    )
    assert price.is_valid_at(now) is True
    assert price.is_valid_at(now - timedelta(days=2)) is False
    assert price.is_valid_at(now + timedelta(days=2)) is False

    inactive_price = Price(
        product_id=uuid4(),
        amount=Decimal("100"),
        status=PriceStatus.DRAFT,
    )
    assert inactive_price.is_valid_at(now) is False
