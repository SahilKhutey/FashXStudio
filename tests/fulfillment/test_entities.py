from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.errors import ValidationError
from fashx.domain.fulfillment.entities import (
    AddressSnapshot,
    Fulfillment,
    FulfillmentLine,
    Shipment,
    ShipmentPackage,
)


def valid_address() -> AddressSnapshot:
    return AddressSnapshot(
        recipient_name="Test User",
        address_line_1="123 Main Street",
        city="Raipur",
        state="Chhattisgarh",
        postal_code="492001",
        country="IN",
    )


def test_address_validation() -> None:
    address = valid_address()
    address.validate()

    # Empty required field
    bad_address = AddressSnapshot(
        recipient_name="",
        address_line_1="123 Main Street",
        city="Raipur",
        state="Chhattisgarh",
        postal_code="492001",
    )
    with pytest.raises(
        ValidationError, match="recipient_name is required"
    ):
        bad_address.validate()


def test_fulfillment_requires_order() -> None:
    fulfillment = Fulfillment(
        address=valid_address(),
    )
    with pytest.raises(
        ValidationError, match="Fulfillment requires order ID"
    ):
        fulfillment.validate()


def test_fulfillment_requires_address() -> None:
    fulfillment = Fulfillment(
        order_id=uuid4(),
    )
    with pytest.raises(
        ValidationError, match="Fulfillment requires delivery address"
    ):
        fulfillment.validate()


def test_fulfillment_valid() -> None:
    fulfillment = Fulfillment(
        order_id=uuid4(),
        address=valid_address(),
    )
    fulfillment.validate()

    orig_version = fulfillment.version
    fulfillment.touch()
    assert fulfillment.version == orig_version + 1


def test_fulfillment_line_validation() -> None:
    # Missing fulfillment_id
    l1 = FulfillmentLine(order_line_id=uuid4(), product_id=uuid4())
    with pytest.raises(
        ValidationError, match="Fulfillment line requires fulfillment ID"
    ):
        l1.validate()

    # Missing order_line_id
    l2 = FulfillmentLine(fulfillment_id=uuid4(), product_id=uuid4())
    with pytest.raises(
        ValidationError, match="Fulfillment line requires order line ID"
    ):
        l2.validate()

    # Missing product_id
    l3 = FulfillmentLine(fulfillment_id=uuid4(), order_line_id=uuid4())
    with pytest.raises(
        ValidationError, match="Fulfillment line requires product ID"
    ):
        l3.validate()

    # Quantity < 1
    l4 = FulfillmentLine(
        fulfillment_id=uuid4(),
        order_line_id=uuid4(),
        product_id=uuid4(),
        quantity=0,
    )
    with pytest.raises(
        ValidationError, match="Fulfillment quantity must be at least 1"
    ):
        l4.validate()

    valid_line = FulfillmentLine(
        fulfillment_id=uuid4(),
        order_line_id=uuid4(),
        product_id=uuid4(),
        quantity=3,
    )
    valid_line.validate()


def test_shipment_package_validation() -> None:
    p1 = ShipmentPackage(weight_grams=100)
    with pytest.raises(
        ValidationError, match="Package requires shipment ID"
    ):
        p1.validate()

    p2 = ShipmentPackage(shipment_id=uuid4(), weight_grams=-1)
    with pytest.raises(
        ValidationError, match="Package weight cannot be negative"
    ):
        p2.validate()

    valid_pkg = ShipmentPackage(shipment_id=uuid4(), weight_grams=500)
    valid_pkg.validate()


def test_shipment_validation_and_touch() -> None:
    # Missing fulfillment_id
    s1 = Shipment(carrier="Delhivery")
    with pytest.raises(
        ValidationError, match="Shipment requires fulfillment ID"
    ):
        s1.validate()

    # Empty carrier
    s2 = Shipment(fulfillment_id=uuid4(), carrier="")
    with pytest.raises(
        ValidationError, match="Shipment carrier is required"
    ):
        s2.validate()

    # Valid shipment
    valid_shipment = Shipment(
        fulfillment_id=uuid4(),
        carrier="BlueDart",
    )
    valid_shipment.validate()

    orig_version = valid_shipment.version
    valid_shipment.touch()
    assert valid_shipment.version == orig_version + 1
