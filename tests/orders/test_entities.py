from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.errors import ValidationError
from fashx.domain.order.entities import (
    Order,
    OrderAddressSnapshot,
    OrderLine,
)


def test_order_validates():
    order = Order(
        order_number="FX-TEST-001",
        shipping_address=(
            OrderAddressSnapshot(
                recipient_name="Test User",
                address_line_1="Main Street",
                city="Raipur",
                state="Chhattisgarh",
                postal_code="492001",
            )
        ),
    )
    order.validate()


def test_order_line_calculation():
    line = OrderLine(
        order_id=uuid4(),
        product_id=uuid4(),
        title="Test Product",
        quantity=2,
        unit_price=Decimal("500"),
    )
    line.validate()
    assert line.subtotal == Decimal("1000.00")
    assert line.total == Decimal("1000.00")


def test_order_validation_missing_order_number():
    order = Order(
        order_number="",
        shipping_address=OrderAddressSnapshot(
            recipient_name="Test",
            address_line_1="Street",
            city="City",
            state="State",
            postal_code="123456",
        ),
    )
    with pytest.raises(ValidationError, match="Order number is required"):
        order.validate()


def test_order_validation_missing_shipping_address():
    order = Order(
        order_number="FX-001",
        shipping_address=None,
    )
    with pytest.raises(ValidationError, match="Shipping address is required"):
        order.validate()


def test_address_snapshot_validation():
    addr = OrderAddressSnapshot(
        recipient_name="",
        address_line_1="Street",
        city="City",
        state="State",
        postal_code="123456",
    )
    with pytest.raises(ValidationError, match="recipient_name is required"):
        addr.validate()


def test_order_line_validation_errors():
    with pytest.raises(ValidationError, match="Order line requires order_id"):
        OrderLine(product_id=uuid4(), title="Prod").validate()

    with pytest.raises(ValidationError, match="Order line requires product_id"):
        OrderLine(order_id=uuid4(), title="Prod").validate()

    with pytest.raises(ValidationError, match="Order line title is required"):
        OrderLine(order_id=uuid4(), product_id=uuid4(), title="").validate()

    with pytest.raises(ValidationError, match="Quantity must be at least 1"):
        OrderLine(order_id=uuid4(), product_id=uuid4(), title="Prod", quantity=0).validate()

    with pytest.raises(ValidationError, match="Unit price cannot be negative"):
        OrderLine(order_id=uuid4(), product_id=uuid4(), title="Prod", unit_price=Decimal("-1")).validate()

    with pytest.raises(ValidationError, match="Discount cannot be negative"):
        OrderLine(order_id=uuid4(), product_id=uuid4(), title="Prod", discount=Decimal("-1")).validate()

    with pytest.raises(ValidationError, match="Currency must be 3 characters"):
        OrderLine(order_id=uuid4(), product_id=uuid4(), title="Prod", currency="TOOLONG").validate()


def test_order_calculate_totals_and_touch():
    order = Order(
        order_number="FX-TOTALS-001",
        shipping_address=OrderAddressSnapshot(
            recipient_name="Test",
            address_line_1="Street",
            city="City",
            state="State",
            postal_code="123456",
        ),
        shipping_total=Decimal("100.00"),
        tax_total=Decimal("50.00"),
    )

    line1 = OrderLine(
        order_id=order.id,
        product_id=uuid4(),
        title="Item 1",
        quantity=2,
        unit_price=Decimal("400.00"),
        discount=Decimal("50.00"),
    )
    line1.validate()

    line2 = OrderLine(
        order_id=order.id,
        product_id=uuid4(),
        title="Item 2",
        quantity=1,
        unit_price=Decimal("600.00"),
        discount=Decimal("0.00"),
    )
    line2.validate()

    order.calculate_totals([line1, line2])
    # subtotal = 800 + 600 = 1400.00
    # discount_total = 50 + 0 = 50.00
    # grand_total = 1400 - 50 + 100 + 50 = 1500.00
    assert order.subtotal == Decimal("1400.00")
    assert order.discount_total == Decimal("50.00")
    assert order.grand_total == Decimal("1500.00")
    assert order.total == Decimal("1500.00")

    orig_version = order.version
    order.touch()
    assert order.version == orig_version + 1
