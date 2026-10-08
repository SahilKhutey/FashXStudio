from decimal import Decimal
from uuid import uuid4

import pytest

from fashx.core.context import CoreContext
from fashx.core.errors import ConflictError, NotFoundError
from fashx.core.event_bus import EventBus
from fashx.domain.order.entities import (
    Order,
    OrderAddressSnapshot,
    OrderLine,
)
from fashx.domain.order.enums import OrderStatus
from fashx.domain.order.events import (
    OrderCancelled,
    OrderCreated,
    OrderStatusChanged,
)
from fashx.domain.order.service import (
    OrderService,
)
from fashx.repositories.order.memory import (
    InMemoryOrderLineRepository,
    InMemoryOrderRepository,
)


@pytest.mark.asyncio
async def test_create_order():
    bus = EventBus()
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    bus.subscribe("OrderCreated", handler)

    service = OrderService(
        order_repository=InMemoryOrderRepository(),
        line_repository=InMemoryOrderLineRepository(),
        event_bus=bus,
    )

    order = Order(
        order_number="FX-TEST-100",
        customer_id=uuid4(),
        shipping_address=(
            OrderAddressSnapshot(
                recipient_name="Customer",
                address_line_1="Street 1",
                city="Raipur",
                state="Chhattisgarh",
                postal_code="492001",
            )
        ),
    )

    line = OrderLine(
        product_id=uuid4(),
        title="Fashion Product",
        quantity=2,
        unit_price=Decimal("750"),
    )

    result = await service.create_order(
        context=CoreContext.create(),
        order=order,
        lines=[line],
    )

    assert result.id == order.id
    assert result.subtotal == Decimal("1500.00")
    assert result.grand_total == Decimal("1500.00")
    assert len(events) == 1
    assert isinstance(events[0], OrderCreated)
    assert events[0].entity_id == order.id


@pytest.mark.asyncio
async def test_order_creation_is_idempotent():
    repository = InMemoryOrderRepository()
    line_repository = InMemoryOrderLineRepository()

    service = OrderService(
        order_repository=repository,
        line_repository=line_repository,
        event_bus=EventBus(),
    )

    order = Order(
        order_number="FX-IDEMPOTENT-001",
        shipping_address=(
            OrderAddressSnapshot(
                recipient_name="Customer",
                address_line_1="Street",
                city="Raipur",
                state="Chhattisgarh",
                postal_code="492001",
            )
        ),
    )

    line = OrderLine(
        product_id=uuid4(),
        title="Product",
        quantity=1,
        unit_price=Decimal("1000"),
    )

    first = await service.create_order(
        context=CoreContext.create(),
        order=order,
        lines=[line],
    )

    second = await service.create_order(
        context=CoreContext.create(),
        order=order,
        lines=[line],
    )

    assert first.id == second.id


@pytest.mark.asyncio
async def test_create_order_empty_lines_raises_conflict():
    service = OrderService(
        order_repository=InMemoryOrderRepository(),
        line_repository=InMemoryOrderLineRepository(),
        event_bus=EventBus(),
    )
    order = Order(
        order_number="FX-EMPTY-001",
        shipping_address=OrderAddressSnapshot(
            recipient_name="Test",
            address_line_1="Line 1",
            city="City",
            state="State",
            postal_code="123456",
        ),
    )
    with pytest.raises(ConflictError, match="Order must contain at least one line"):
        await service.create_order(context=CoreContext.create(), order=order, lines=[])


@pytest.mark.asyncio
async def test_create_order_currency_mismatch_raises_conflict():
    service = OrderService(
        order_repository=InMemoryOrderRepository(),
        line_repository=InMemoryOrderLineRepository(),
        event_bus=EventBus(),
    )
    order = Order(
        order_number="FX-CURR-001",
        currency="INR",
        shipping_address=OrderAddressSnapshot(
            recipient_name="Test",
            address_line_1="Line 1",
            city="City",
            state="State",
            postal_code="123456",
        ),
    )
    line = OrderLine(
        product_id=uuid4(),
        title="Prod",
        currency="USD",
        unit_price=Decimal("50"),
    )
    with pytest.raises(ConflictError, match="Order line currency mismatch"):
        await service.create_order(context=CoreContext.create(), order=order, lines=[line])


@pytest.mark.asyncio
async def test_get_order_and_change_status():
    bus = EventBus()
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    for event_name in ["OrderStatusChanged", "OrderCancelled", "OrderCompleted"]:
        bus.subscribe(event_name, handler)

    service = OrderService(
        order_repository=InMemoryOrderRepository(),
        line_repository=InMemoryOrderLineRepository(),
        event_bus=bus,
    )

    order = Order(
        order_number="FX-STATUS-001",
        shipping_address=OrderAddressSnapshot(
            recipient_name="Customer",
            address_line_1="Street",
            city="Raipur",
            state="Chhattisgarh",
            postal_code="492001",
        ),
    )
    line = OrderLine(
        product_id=uuid4(),
        title="Product",
        quantity=1,
        unit_price=Decimal("500"),
    )
    await service.create_order(context=CoreContext.create(), order=order, lines=[line])

    # Get order
    fetched = await service.get_order(order.id)
    assert fetched.id == order.id

    # Not found
    with pytest.raises(NotFoundError, match="Order not found"):
        await service.get_order(uuid4())

    # Change status PENDING -> CONFIRMED
    updated = await service.change_status(
        context=CoreContext.create(),
        order_id=order.id,
        target=OrderStatus.CONFIRMED,
    )
    assert updated.status == OrderStatus.CONFIRMED

    # Change status CONFIRMED -> CANCELLED
    cancelled = await service.change_status(
        context=CoreContext.create(),
        order_id=order.id,
        target=OrderStatus.CANCELLED,
    )
    assert cancelled.status == OrderStatus.CANCELLED

    # Check events
    status_changed_events = [e for e in events if isinstance(e, OrderStatusChanged)]
    assert len(status_changed_events) == 2
    cancelled_events = [e for e in events if isinstance(e, OrderCancelled)]
    assert len(cancelled_events) == 1
