from decimal import Decimal

import pytest

from app.core.errors import ValidationError
from fashx.domain.pricing.enums import Currency
from fashx.domain.pricing.money import money


def test_money_creation_and_quantization():
    m = money("100", Currency.INR)
    assert m.amount == Decimal("100.00")
    assert m.currency == Currency.INR


def test_money_subtraction():
    m1 = money("2000", Currency.INR)
    m2 = money("400", Currency.INR)
    diff = m1.subtract(m2)
    assert diff.amount == Decimal("1600.00")
    assert diff.currency == Currency.INR


def test_money_currency_mismatch():
    m1 = money("100", Currency.INR)
    m2 = money("100", Currency.USD)
    with pytest.raises(ValidationError):
        m1.subtract(m2)
