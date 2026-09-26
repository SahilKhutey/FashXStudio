from __future__ import annotations

from uuid import uuid4

import pytest

from app.domain.fulfillment.entities import (
    AddressSnapshot,
    Fulfillment,
    FulfillmentLine,
    Shipment,
    ShipmentPackage,
)
from app.repositories.fulfillment.memory import (
    InMemoryFulfillmentLineRepository,
    InMemoryFulfillmentRepository,
    InMemoryShipmentPackageRepository,
    InMemoryShipmentRepository,
)


def sample_address() -> AddressSnapshot:
    return AddressSnapshot(
        recipient_name="Customer Name",
        address_line_1="101 Tech Park",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560001",
    )


@pytest.mark.asyncio
async def test_fulfillment_repository_crud() -> None:
    repo = InMemoryFulfillmentRepository()
    order_id = uuid4()

    ful = Fulfillment(
        order_id=order_id,
        address=sample_address(),
    )
    await repo.save(ful)

    fetched = await repo.get(ful.id)
    assert fetched is not None
    assert fetched.id == ful.id
    assert fetched.order_id == order_id

    by_order = await repo.list_by_order(order_id)
    assert len(by_order) == 1
    assert by_order[0].id == ful.id

    assert await repo.get(uuid4()) is None
    assert len(await repo.list_by_order(uuid4())) == 0


@pytest.mark.asyncio
async def test_fulfillment_line_repository_crud() -> None:
    repo = InMemoryFulfillmentLineRepository()
    fulfillment_id1 = uuid4()
    fulfillment_id2 = uuid4()

    line1 = FulfillmentLine(
        fulfillment_id=fulfillment_id1,
        order_line_id=uuid4(),
        product_id=uuid4(),
        quantity=1,
    )
    line2 = FulfillmentLine(
        fulfillment_id=fulfillment_id1,
        order_line_id=uuid4(),
        product_id=uuid4(),
        quantity=2,
    )
    line3 = FulfillmentLine(
        fulfillment_id=fulfillment_id2,
        order_line_id=uuid4(),
        product_id=uuid4(),
        quantity=5,
    )

    await repo.save(line1)
    await repo.save(line2)
    await repo.save(line3)

    list1 = await repo.list_by_fulfillment(fulfillment_id1)
    assert len(list1) == 2
    assert {line.id for line in list1} == {line1.id, line2.id}

    list2 = await repo.list_by_fulfillment(fulfillment_id2)
    assert len(list2) == 1
    assert list2[0].id == line3.id

    assert len(await repo.list_by_fulfillment(uuid4())) == 0


@pytest.mark.asyncio
async def test_shipment_repository_crud() -> None:
    repo = InMemoryShipmentRepository()
    fulfillment_id = uuid4()

    shipment = Shipment(
        fulfillment_id=fulfillment_id,
        carrier="BlueDart",
    )
    await repo.save(shipment)

    fetched = await repo.get(shipment.id)
    assert fetched is not None
    assert fetched.id == shipment.id

    by_ful = await repo.list_by_fulfillment(fulfillment_id)
    assert len(by_ful) == 1
    assert by_ful[0].id == shipment.id

    assert await repo.get(uuid4()) is None
    assert len(await repo.list_by_fulfillment(uuid4())) == 0


@pytest.mark.asyncio
async def test_shipment_package_repository_crud() -> None:
    repo = InMemoryShipmentPackageRepository()
    shipment_id = uuid4()

    pkg1 = ShipmentPackage(
        shipment_id=shipment_id,
        weight_grams=500,
    )
    pkg2 = ShipmentPackage(
        shipment_id=shipment_id,
        weight_grams=800,
    )
    await repo.save(pkg1)
    await repo.save(pkg2)

    by_shipment = await repo.list_by_shipment(shipment_id)
    assert len(by_shipment) == 2
    assert {pkg.id for pkg in by_shipment} == {pkg1.id, pkg2.id}

    assert len(await repo.list_by_shipment(uuid4())) == 0
