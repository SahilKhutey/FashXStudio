from decimal import Decimal
from uuid import uuid4

import pytest

from fashx.domain.order.entities import (
    Order,
    OrderAddressSnapshot,
    OrderLine,
)
from fashx.repositories.order.memory import (
    InMemoryOrderLineRepository,
    InMemoryOrderRepository,
)


@pytest.mark.asyncio
async def test_in_memory_order_repository():
    repo = InMemoryOrderRepository()
    customer_id = uuid4()

    order = Order(
        order_number="FX-REPO-001",
        customer_id=customer_id,
        shipping_address=OrderAddressSnapshot(
            recipient_name="Customer",
            address_line_1="Main Street",
            city="Raipur",
            state="Chhattisgarh",
            postal_code="492001",
        ),
    )

    await repo.save(order)

    # Get by ID
    fetched = await repo.get(order.id)
    assert fetched is not None
    assert fetched.id == order.id

    # Get by order number
    by_number = await repo.get_by_number("FX-REPO-001")
    assert by_number is not None
    assert by_number.id == order.id

    # List by customer
    orders = await repo.list_by_customer(customer_id)
    assert len(orders) == 1
    assert orders[0].id == order.id

    # Non-existent
    assert await repo.get(uuid4()) is None
    assert await repo.get_by_number("NON-EXISTENT") is None


@pytest.mark.asyncio
async def test_in_memory_order_line_repository():
    repo = InMemoryOrderLineRepository()
    order_id = uuid4()

    line1 = OrderLine(
        order_id=order_id,
        product_id=uuid4(),
        title="Item 1",
        quantity=1,
        unit_price=Decimal("100"),
    )
    line2 = OrderLine(
        order_id=order_id,
        product_id=uuid4(),
        title="Item 2",
        quantity=2,
        unit_price=Decimal("200"),
    )
    other_line = OrderLine(
        order_id=uuid4(),
        product_id=uuid4(),
        title="Other",
    )

    await repo.save(line1)
    await repo.save(line2)
    await repo.save(other_line)

    lines = await repo.list_by_order(order_id)
    assert len(lines) == 2
    ids = {item.id for item in lines}
    assert line1.id in ids
    assert line2.id in ids
