from decimal import Decimal

import pytest

from fashx.core.errors import ValidationError
from fashx.domain.pricing.enums import Currency
from fashx.domain.pricing.money import money
from fashx.domain.promotions.enums import (
    DiscountType,
)
from fashx.domain.promotions.service import (
    calculate_discount,
)


def test_percentage_discount():
    price = money(
        "2000",
        Currency.INR,
    )

    result = calculate_discount(
        base_price=price,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("20"),
    )

    assert result.amount == Decimal("400.00")


def test_fixed_discount():
    price = money(
        "2000",
        Currency.INR,
    )

    result = calculate_discount(
        base_price=price,
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("500"),
    )

    assert result.amount == Decimal("500.00")


def test_discount_cannot_exceed_price():
    price = money(
        "500",
        Currency.INR,
    )

    result = calculate_discount(
        base_price=price,
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("1000"),
    )

    assert result.amount == Decimal("500.00")


def test_percentage_above_100_rejected():
    price = money(
        "1000",
        Currency.INR,
    )

    with pytest.raises(ValidationError):
        calculate_discount(
            base_price=price,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("101"),
        )


def test_negative_discount_rejected():
    price = money("1000", Currency.INR)
    with pytest.raises(ValidationError):
        calculate_discount(
            base_price=price,
            discount_type=DiscountType.FIXED,
            discount_value=Decimal("-10"),
        )


def test_maximum_discount_cap():
    price = money("2000", Currency.INR)
    result = calculate_discount(
        base_price=price,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("50"),  # 50% of 2000 is 1000
        maximum_discount=Decimal("300"),  # capped at 300
    )
    assert result.amount == Decimal("300.00")
