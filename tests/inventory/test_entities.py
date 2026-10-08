from uuid import uuid4

import pytest

from fashx.core.errors import ValidationError
from fashx.domain.inventory.entities import (
    InventoryItem,
    StockLocation,
)
from fashx.domain.inventory.enums import (
    AvailabilityStatus,
    InventoryStatus,
)


def test_inventory_validates():
    item = InventoryItem(
        variant_id=uuid4(),
        location_id=uuid4(),
        status=InventoryStatus.ACTIVE,
        on_hand=100,
        reserved=20,
    )
    item.validate()

    assert item.available == 80
    assert item.availability == AvailabilityStatus.AVAILABLE


def test_reserved_cannot_exceed_on_hand():
    item = InventoryItem(
        variant_id=uuid4(),
        location_id=uuid4(),
        on_hand=10,
        reserved=20,
    )
    with pytest.raises(ValidationError):
        item.validate()


def test_negative_stock_rejected():
    item = InventoryItem(
        variant_id=uuid4(),
        location_id=uuid4(),
        on_hand=-5,
    )
    with pytest.raises(ValidationError):
        item.validate()


def test_negative_reserved_rejected():
    item = InventoryItem(
        variant_id=uuid4(),
        location_id=uuid4(),
        on_hand=10,
        reserved=-1,
    )
    with pytest.raises(ValidationError):
        item.validate()


def test_negative_incoming_rejected():
    item = InventoryItem(
        variant_id=uuid4(),
        location_id=uuid4(),
        on_hand=10,
        incoming=-2,
    )
    with pytest.raises(ValidationError):
        item.validate()


def test_missing_variant_id_rejected():
    item = InventoryItem(
        variant_id=None,
        location_id=uuid4(),
        on_hand=10,
    )
    with pytest.raises(ValidationError):
        item.validate()


def test_missing_location_id_rejected():
    item = InventoryItem(
        variant_id=uuid4(),
        location_id=None,
        on_hand=10,
    )
    with pytest.raises(ValidationError):
        item.validate()


def test_low_stock():
    item = InventoryItem(
        variant_id=uuid4(),
        location_id=uuid4(),
        status=InventoryStatus.ACTIVE,
        on_hand=10,
        reserved=6,
        low_stock_threshold=5,
    )
    assert item.available == 4
    assert item.availability == AvailabilityStatus.LOW_STOCK


def test_out_of_stock():
    item = InventoryItem(
        variant_id=uuid4(),
        location_id=uuid4(),
        status=InventoryStatus.ACTIVE,
        on_hand=10,
        reserved=10,
    )
    assert item.available == 0
    assert item.availability == AvailabilityStatus.OUT_OF_STOCK


def test_unavailable_when_not_active():
    item = InventoryItem(
        variant_id=uuid4(),
        location_id=uuid4(),
        status=InventoryStatus.DRAFT,
        on_hand=100,
        reserved=0,
    )
    assert item.available == 100
    assert item.availability == AvailabilityStatus.UNAVAILABLE

    item.status = InventoryStatus.PAUSED
    assert item.availability == AvailabilityStatus.UNAVAILABLE


def test_location_requires_name():
    location = StockLocation(
        name="",
        code="WH-01",
    )
    with pytest.raises(ValidationError):
        location.validate()


def test_location_requires_code():
    location = StockLocation(
        name="Warehouse",
        code="",
    )
    with pytest.raises(ValidationError):
        location.validate()


def test_location_touch_and_version():
    location = StockLocation(
        name="Warehouse 1",
        code="WH-1",
    )
    v1 = location.version
    t1 = location.updated_at
    location.touch()
    assert location.version == v1 + 1
    assert location.updated_at >= t1
