from decimal import Decimal
from uuid import uuid4

import pytest

from fashx.core.context import CoreContext
from fashx.core.errors import ConflictError, NotFoundError
from fashx.core.event_bus import EventBus
from fashx.domain.checkout.entities import CheckoutSession
from fashx.domain.checkout.enums import CheckoutStatus
from fashx.domain.checkout.events import (
    CheckoutCreated,
    CheckoutValidated,
)
from fashx.domain.checkout.service import CheckoutService
from fashx.domain.order.entities import (
    Order,
    OrderAddressSnapshot,
    OrderLine,
)
from fashx.domain.order.service import OrderService
from fashx.repositories.checkout.memory import InMemoryCheckoutRepository
from fashx.repositories.order.memory import (
    InMemoryOrderLineRepository,
    InMemoryOrderRepository,
)


@pytest.fixture
def checkout_setup():
    checkout_repo = InMemoryCheckoutRepository()
    order_repo = InMemoryOrderRepository()
    line_repo = InMemoryOrderLineRepository()
    bus = EventBus()
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    for event_name in ["CheckoutCreated", "CheckoutValidated", "OrderCreated"]:
        bus.subscribe(event_name, handler)

    order_service = OrderService(
        order_repository=order_repo,
        line_repository=line_repo,
        event_bus=bus,
    )
    checkout_service = CheckoutService(
        checkout_repository=checkout_repo,
        event_bus=bus,
        order_service=order_service,
    )
    return checkout_service, order_service, events


@pytest.mark.asyncio
async def test_create_and_get_checkout(checkout_setup):
    service, _, events = checkout_setup
    context = CoreContext.create()
    cart_id = uuid4()

    session = CheckoutSession(
        cart_id=cart_id,
        customer_id=uuid4(),
    )

    created = await service.create_checkout(context=context, checkout=session)
    assert created.id == session.id
    assert created.status == CheckoutStatus.OPEN

    # Idempotent retrieval for same cart
    second = await service.create_checkout(
        context=context,
        checkout=CheckoutSession(cart_id=cart_id),
    )
    assert second.id == session.id

    fetched = await service.get_checkout(session.id)
    assert fetched.id == session.id

    with pytest.raises(NotFoundError, match="Checkout not found"):
        await service.get_checkout(uuid4())

    created_events = [e for e in events if isinstance(e, CheckoutCreated)]
    assert len(created_events) == 1
    assert created_events[0].entity_id == session.id


@pytest.mark.asyncio
async def test_validate_checkout(checkout_setup):
    service, _, events = checkout_setup
    context = CoreContext.create()
    session = CheckoutSession(cart_id=uuid4())
    await service.create_checkout(context=context, checkout=session)

    validated = await service.validate_checkout(
        context=context,
        checkout_id=session.id,
    )
    assert validated.status == CheckoutStatus.READY

    val_events = [e for e in events if isinstance(e, CheckoutValidated)]
    assert len(val_events) == 1
    assert val_events[0].entity_id == session.id


@pytest.mark.asyncio
async def test_convert_to_order_lifecycle(checkout_setup):
    service, _, _ = checkout_setup
    context = CoreContext.create()

    session = CheckoutSession(cart_id=uuid4())
    await service.create_checkout(context=context, checkout=session)

    order = Order(
        order_number="FX-CONVERT-001",
        shipping_address=OrderAddressSnapshot(
            recipient_name="Customer",
            address_line_1="Road 1",
            city="Raipur",
            state="Chhattisgarh",
            postal_code="492001",
        ),
    )
    lines = [
        OrderLine(
            product_id=uuid4(),
            title="Dress",
            quantity=1,
            unit_price=Decimal("1200"),
        )
    ]

    # Cannot convert when OPEN (not READY)
    with pytest.raises(ConflictError, match="Checkout is not ready"):
        await service.convert_to_order(
            context=context,
            checkout_id=session.id,
            order=order,
            lines=lines,
        )

    # Validate first -> READY
    await service.validate_checkout(context=context, checkout_id=session.id)

    # Now convert succeeds
    created_order = await service.convert_to_order(
        context=context,
        checkout_id=session.id,
        order=order,
        lines=lines,
    )

    assert created_order.id == order.id
    assert created_order.grand_total == Decimal("1200.00")

    # Check updated checkout session state
    refreshed_checkout = await service.get_checkout(session.id)
    assert refreshed_checkout.status == CheckoutStatus.PAYMENT_PENDING
    assert refreshed_checkout.order_id == created_order.id
