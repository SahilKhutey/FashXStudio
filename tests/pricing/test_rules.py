from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.errors import ValidationError
from app.domain.pricing.entities import PricingRule
from app.domain.pricing.enums import DiscountType, RuleScope, RuleStatus
from app.domain.pricing.rules import (
    PricingContext,
    calculate_discount,
    rule_matches,
    rule_valid_at,
)


def test_rule_validation_empty_name():
    rule = PricingRule(name="")
    with pytest.raises(ValidationError, match="Pricing rule name is required"):
        rule.validate()


def test_rule_validation_negative_discount():
    rule = PricingRule(name="Discount", discount_value=Decimal("-10"))
    with pytest.raises(ValidationError, match="Discount value cannot be negative"):
        rule.validate()


def test_rule_validation_percentage_discount_over_100():
    rule = PricingRule(
        name="Discount",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("105"),
    )
    with pytest.raises(ValidationError, match="Percentage discount cannot exceed 100"):
        rule.validate()


def test_rule_validation_negative_priority():
    rule = PricingRule(name="Discount", priority=-1)
    with pytest.raises(ValidationError, match="Priority cannot be negative"):
        rule.validate()


def test_rule_validation_invalid_minimum_quantity():
    rule = PricingRule(name="Discount", minimum_quantity=0)
    with pytest.raises(ValidationError, match="Minimum quantity must be positive"):
        rule.validate()


def test_rule_validation_invalid_minimum_cart_value():
    rule = PricingRule(name="Discount", minimum_cart_value=Decimal("-5"))
    with pytest.raises(ValidationError, match="Minimum cart value cannot be negative"):
        rule.validate()


def test_rule_validation_invalid_validity_window():
    now = datetime.now(UTC)
    rule = PricingRule(
        name="Discount",
        valid_from=now,
        valid_until=now - timedelta(days=1),
    )
    with pytest.raises(ValidationError, match="Rule validity window is invalid"):
        rule.validate()


def test_rule_validation_and_touch():
    rule = PricingRule(
        name="Summer Sale",
        scope=RuleScope.PRODUCT,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("15"),
    )
    rule.validate()
    assert rule.version == 1
    rule.touch()
    assert rule.version == 2


def test_calculate_discount_percentage():
    rule = PricingRule(
        name="10% Off",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("10"),
    )
    discount = calculate_discount(Decimal("250.00"), rule)
    assert discount == Decimal("25.00")


def test_calculate_discount_fixed():
    rule = PricingRule(
        name="50 Off",
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("50.00"),
    )
    discount = calculate_discount(Decimal("250.00"), rule)
    assert discount == Decimal("50.00")


def test_calculate_discount_capped_at_amount():
    rule = PricingRule(
        name="High Fixed Off",
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("500.00"),
    )
    discount = calculate_discount(Decimal("100.00"), rule)
    assert discount == Decimal("100.00")


def test_rule_matches_scope_and_conditions():
    prod_id = uuid4()
    var_id = uuid4()
    list_id = uuid4()
    cust_id = uuid4()

    rule = PricingRule(
        name="VIP Rule",
        product_id=prod_id,
        variant_id=var_id,
        listing_id=list_id,
        customer_id=cust_id,
        region="IN-MH",
        minimum_quantity=3,
        minimum_cart_value=Decimal("1000.00"),
    )

    valid_context = PricingContext(
        product_id=prod_id,
        variant_id=var_id,
        listing_id=list_id,
        customer_id=cust_id,
        region="in-mh",
        quantity=3,
        cart_value=Decimal("1500.00"),
    )
    assert rule_matches(rule, valid_context) is True

    # Product mismatch
    assert rule_matches(rule, PricingContext(product_id=uuid4())) is False

    # Variant mismatch
    assert (
        rule_matches(
            rule,
            PricingContext(
                product_id=prod_id,
                variant_id=uuid4(),
            ),
        )
        is False
    )

    # Quantity too low
    low_qty_context = PricingContext(
        product_id=prod_id,
        variant_id=var_id,
        listing_id=list_id,
        customer_id=cust_id,
        region="in-mh",
        quantity=2,
        cart_value=Decimal("1500.00"),
    )
    assert rule_matches(rule, low_qty_context) is False

    # Cart value too low
    low_cart_context = PricingContext(
        product_id=prod_id,
        variant_id=var_id,
        listing_id=list_id,
        customer_id=cust_id,
        region="in-mh",
        quantity=5,
        cart_value=Decimal("500.00"),
    )
    assert rule_matches(rule, low_cart_context) is False


def test_rule_valid_at():
    now = datetime.now(UTC)
    rule = PricingRule(
        name="Active Rule",
        status=RuleStatus.ACTIVE,
        valid_from=now - timedelta(days=1),
        valid_until=now + timedelta(days=1),
    )
    assert rule_valid_at(rule, now) is True
    assert rule_valid_at(rule, now - timedelta(days=2)) is False
    assert rule_valid_at(rule, now + timedelta(days=2)) is False

    draft_rule = PricingRule(
        name="Draft",
        status=RuleStatus.DRAFT,
    )
    assert rule_valid_at(draft_rule, now) is False
