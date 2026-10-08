from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.context import CoreContext
from app.core.errors import NotFoundError, ValidationError
from app.core.event_bus import EventBus
from fashx.domain.cart.entities import Cart, CartLine
from fashx.domain.cart.enums import CartLineStatus, CartOwnerType, CartStatus
from fashx.domain.cart.service import CartService
from fashx.repositories.cart.memory import (
    InMemoryCartLineRepository,
    InMemoryCartRepository,
)


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def service(event_bus: EventBus) -> CartService:
    return CartService(
        cart_repository=InMemoryCartRepository(),
        line_repository=InMemoryCartLineRepository(),
        event_bus=event_bus,
    )


@pytest.mark.asyncio
async def test_create_cart_anonymous(
    service: CartService, event_bus: EventBus
) -> None:
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("CartCreated", handler)

    cart = Cart(
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="guest-session-1",
        currency="USD",
    )
    result = await service.create_cart(
        context=CoreContext.create(),
        cart=cart,
    )

    assert result.id == cart.id
    assert result.session_id == "guest-session-1"
    assert len(events) == 1
    assert events[0].entity_id == cart.id


@pytest.mark.asyncio
async def test_create_cart_customer(
    service: CartService, event_bus: EventBus
) -> None:
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("CartCreated", handler)

    customer_id = uuid4()
    cart = Cart(
        owner_type=CartOwnerType.CUSTOMER,
        customer_id=customer_id,
        currency="EUR",
    )
    result = await service.create_cart(
        context=CoreContext.create(),
        cart=cart,
    )

    assert result.id == cart.id
    assert result.customer_id == customer_id
    assert result.currency == "EUR"
    assert len(events) == 1
    assert events[0].entity_id == cart.id


@pytest.mark.asyncio
async def test_create_cart_idempotent_session(
    service: CartService, event_bus: EventBus
) -> None:
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("CartCreated", handler)

    cart1 = Cart(
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="sess-repeat",
        currency="USD",
    )
    created1 = await service.create_cart(
        context=CoreContext.create(),
        cart=cart1,
    )

    cart2 = Cart(
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="sess-repeat",
        currency="USD",
    )
    created2 = await service.create_cart(
        context=CoreContext.create(),
        cart=cart2,
    )

    assert created2.id == created1.id
    assert len(events) == 1  # Only 1 created event published


@pytest.mark.asyncio
async def test_create_cart_idempotent_customer(service: CartService) -> None:
    customer_id = uuid4()
    cart1 = Cart(
        owner_type=CartOwnerType.CUSTOMER,
        customer_id=customer_id,
        currency="USD",
    )
    created1 = await service.create_cart(
        context=CoreContext.create(),
        cart=cart1,
    )

    cart2 = Cart(
        owner_type=CartOwnerType.CUSTOMER,
        customer_id=customer_id,
        currency="USD",
    )
    created2 = await service.create_cart(
        context=CoreContext.create(),
        cart=cart2,
    )

    assert created2.id == created1.id


@pytest.mark.asyncio
async def test_get_cart_success_and_not_found(service: CartService) -> None:
    cart = Cart(
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="sess-get",
        currency="USD",
    )
    await service.create_cart(context=CoreContext.create(), cart=cart)

    fetched = await service.get_cart(cart.id)
    assert fetched.id == cart.id

    with pytest.raises(NotFoundError):
        await service.get_cart(uuid4())


@pytest.mark.asyncio
async def test_add_line_success(
    service: CartService, event_bus: EventBus
) -> None:
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("CartLineAdded", handler)

    cart = Cart(
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="sess-add-line",
        currency="USD",
    )
    await service.create_cart(context=CoreContext.create(), cart=cart)

    product_id = uuid4()
    listing_id = uuid4()
    line = CartLine(
        cart_id=cart.id,
        product_id=product_id,
        listing_id=listing_id,
        unit_price=Decimal("120.00"),
        currency="USD",
        quantity=2,
    )

    added = await service.add_line(
        context=CoreContext.create(),
        cart_id=cart.id,
        line=line,
    )

    assert added.id == line.id
    assert added.quantity == 2
    assert len(events) == 1
    assert events[0].entity_id == line.id


@pytest.mark.asyncio
async def test_add_line_duplicate_merge(
    service: CartService, event_bus: EventBus
) -> None:
    events_added = []
    events_qty_changed = []

    async def added_handler(envelope):
        events_added.append(envelope.event)

    async def qty_handler(envelope):
        events_qty_changed.append(envelope.event)

    event_bus.subscribe("CartLineAdded", added_handler)
    event_bus.subscribe("CartLineQuantityChanged", qty_handler)

    cart = Cart(
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="sess-merge",
        currency="USD",
    )
    await service.create_cart(context=CoreContext.create(), cart=cart)

    product_id = uuid4()
    variant_id = uuid4()
    listing_id = uuid4()

    line1 = CartLine(
        cart_id=cart.id,
        product_id=product_id,
        variant_id=variant_id,
        listing_id=listing_id,
        unit_price=Decimal("50.00"),
        currency="USD",
        quantity=2,
    )
    await service.add_line(
        context=CoreContext.create(),
        cart_id=cart.id,
        line=line1,
    )

    line2 = CartLine(
        cart_id=cart.id,
        product_id=product_id,
        variant_id=variant_id,
        listing_id=listing_id,
        unit_price=Decimal("50.00"),
        currency="USD",
        quantity=3,
    )
    merged = await service.add_line(
        context=CoreContext.create(),
        cart_id=cart.id,
        line=line2,
    )

    assert merged.id == line1.id
    assert merged.quantity == 5
    assert len(events_added) == 1
    assert len(events_qty_changed) == 1
    assert events_qty_changed[0].entity_id == line1.id


@pytest.mark.asyncio
async def test_add_line_rejects_currency_mismatch(service: CartService) -> None:
    cart = Cart(
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="sess-currency",
        currency="USD",
    )
    await service.create_cart(context=CoreContext.create(), cart=cart)

    line = CartLine(
        cart_id=cart.id,
        product_id=uuid4(),
        listing_id=uuid4(),
        unit_price=Decimal("25.00"),
        currency="EUR",
        quantity=1,
    )

    with pytest.raises(
        ValidationError, match="Cart line currency must match cart currency"
    ):
        await service.add_line(
            context=CoreContext.create(),
            cart_id=cart.id,
            line=line,
        )


@pytest.mark.asyncio
async def test_add_line_rejects_inactive_or_expired_cart(
    service: CartService,
) -> None:
    cart = Cart(
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="sess-inactive",
        currency="USD",
        status=CartStatus.CHECKOUT,
    )
    await service.cart_repository.save(cart)

    line = CartLine(
        cart_id=cart.id,
        product_id=uuid4(),
        listing_id=uuid4(),
        unit_price=Decimal("15.00"),
        currency="USD",
        quantity=1,
    )

    with pytest.raises(
        ValidationError, match="Items can only be added to an active cart"
    ):
        await service.add_line(
            context=CoreContext.create(),
            cart_id=cart.id,
            line=line,
        )

    # Expired cart
    expired_cart = Cart(
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="sess-expired",
        currency="USD",
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )
    await service.cart_repository.save(expired_cart)

    line2 = CartLine(
        cart_id=expired_cart.id,
        product_id=uuid4(),
        listing_id=uuid4(),
        unit_price=Decimal("15.00"),
        currency="USD",
        quantity=1,
    )
    with pytest.raises(ValidationError, match="Expired cart cannot receive items"):
        await service.add_line(
            context=CoreContext.create(),
            cart_id=expired_cart.id,
            line=line2,
        )


@pytest.mark.asyncio
async def test_add_line_rejects_wrong_cart_id(service: CartService) -> None:
    cart = Cart(
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="sess-mismatch",
        currency="USD",
    )
    await service.create_cart(context=CoreContext.create(), cart=cart)

    line = CartLine(
        cart_id=uuid4(),  # Different cart ID
        product_id=uuid4(),
        listing_id=uuid4(),
        unit_price=Decimal("10.00"),
        currency="USD",
        quantity=1,
    )

    with pytest.raises(
        ValidationError, match="Cart line does not belong to cart"
    ):
        await service.add_line(
            context=CoreContext.create(),
            cart_id=cart.id,
            line=line,
        )


@pytest.mark.asyncio
async def test_update_quantity(service: CartService, event_bus: EventBus) -> None:
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("CartLineQuantityChanged", handler)

    cart = Cart(
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="sess-qty",
        currency="USD",
    )
    await service.create_cart(context=CoreContext.create(), cart=cart)

    line = CartLine(
        cart_id=cart.id,
        product_id=uuid4(),
        listing_id=uuid4(),
        unit_price=Decimal("30.00"),
        currency="USD",
        quantity=1,
    )
    await service.add_line(context=CoreContext.create(), cart_id=cart.id, line=line)

    updated = await service.update_quantity(
        context=CoreContext.create(),
        line_id=line.id,
        quantity=4,
    )

    assert updated.quantity == 4
    assert len(events) == 1
    assert events[0].entity_id == line.id

    with pytest.raises(NotFoundError):
        await service.update_quantity(
            context=CoreContext.create(),
            line_id=uuid4(),
            quantity=2,
        )

    with pytest.raises(ValidationError, match="Quantity must be at least 1"):
        await service.update_quantity(
            context=CoreContext.create(),
            line_id=line.id,
            quantity=0,
        )


@pytest.mark.asyncio
async def test_remove_line(service: CartService, event_bus: EventBus) -> None:
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("CartLineRemoved", handler)

    cart = Cart(
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="sess-remove",
        currency="USD",
    )
    await service.create_cart(context=CoreContext.create(), cart=cart)

    line = CartLine(
        cart_id=cart.id,
        product_id=uuid4(),
        listing_id=uuid4(),
        unit_price=Decimal("30.00"),
        currency="USD",
        quantity=1,
    )
    await service.add_line(context=CoreContext.create(), cart_id=cart.id, line=line)

    removed = await service.remove_line(
        context=CoreContext.create(),
        line_id=line.id,
    )

    assert removed.status == CartLineStatus.REMOVED
    assert len(events) == 1
    assert events[0].entity_id == line.id

    with pytest.raises(NotFoundError):
        await service.remove_line(
            context=CoreContext.create(),
            line_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_clear_cart_and_totals(
    service: CartService, event_bus: EventBus
) -> None:
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("CartCleared", handler)

    cart = Cart(
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="sess-totals",
        currency="USD",
    )
    await service.create_cart(context=CoreContext.create(), cart=cart)

    line1 = CartLine(
        cart_id=cart.id,
        product_id=uuid4(),
        listing_id=uuid4(),
        unit_price=Decimal("15.50"),
        currency="USD",
        quantity=2,
    )
    line2 = CartLine(
        cart_id=cart.id,
        product_id=uuid4(),
        listing_id=uuid4(),
        unit_price=Decimal("40.00"),
        currency="USD",
        quantity=1,
    )

    await service.add_line(context=CoreContext.create(), cart_id=cart.id, line=line1)
    await service.add_line(context=CoreContext.create(), cart_id=cart.id, line=line2)

    totals = await service.calculate_totals(cart.id)
    assert totals.item_count == 3
    assert totals.subtotal == Decimal("71.00")
    assert totals.currency == "USD"

    await service.clear_cart(context=CoreContext.create(), cart_id=cart.id)
    assert len(events) == 1
    assert events[0].entity_id == cart.id

    totals_after_clear = await service.calculate_totals(cart.id)
    assert totals_after_clear.item_count == 0
    assert totals_after_clear.subtotal == Decimal("0")


@pytest.mark.asyncio
async def test_change_status(service: CartService, event_bus: EventBus) -> None:
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("CartStatusChanged", handler)

    cart = Cart(
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="sess-status",
        currency="USD",
    )
    await service.create_cart(context=CoreContext.create(), cart=cart)

    updated = await service.change_status(
        context=CoreContext.create(),
        cart_id=cart.id,
        target=CartStatus.CHECKOUT,
    )
    assert updated.status == CartStatus.CHECKOUT
    assert len(events) == 1
    assert events[0].entity_id == cart.id

    # CONVERTED
    converted = await service.change_status(
        context=CoreContext.create(),
        cart_id=cart.id,
        target=CartStatus.CONVERTED,
    )
    assert converted.status == CartStatus.CONVERTED

    # CONVERTED cannot go to ACTIVE
    with pytest.raises(ValidationError, match="Invalid cart status transition"):
        await service.change_status(
            context=CoreContext.create(),
            cart_id=cart.id,
            target=CartStatus.ACTIVE,
        )
