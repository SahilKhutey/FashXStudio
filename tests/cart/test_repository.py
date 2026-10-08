from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from fashx.domain.cart.entities import Cart, CartLine
from fashx.domain.cart.enums import CartLineStatus, CartOwnerType, CartStatus
from fashx.repositories.cart.memory import (
    InMemoryCartLineRepository,
    InMemoryCartRepository,
)


@pytest.mark.asyncio
async def test_cart_repository_save_and_get() -> None:
    repo = InMemoryCartRepository()
    cart_id = uuid4()
    cart = Cart(
        id=cart_id,
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="session-123",
        currency="USD",
    )
    saved = await repo.save(cart)
    assert saved.id == cart_id

    fetched = await repo.get(cart_id)
    assert fetched is not None
    assert fetched.id == cart_id
    assert fetched.session_id == "session-123"

    missing = await repo.get(uuid4())
    assert missing is None


@pytest.mark.asyncio
async def test_cart_repository_get_active_by_session() -> None:
    repo = InMemoryCartRepository()
    cart = Cart(
        id=uuid4(),
        owner_type=CartOwnerType.ANONYMOUS,
        session_id="sess-abc",
        currency="USD",
        status=CartStatus.ACTIVE,
    )
    await repo.save(cart)

    active = await repo.get_active_by_session("sess-abc")
    assert active is not None
    assert active.id == cart.id

    assert await repo.get_active_by_session("sess-xyz") is None

    # Deactivated cart
    cart.status = CartStatus.CONVERTED
    await repo.save(cart)
    assert await repo.get_active_by_session("sess-abc") is None


@pytest.mark.asyncio
async def test_cart_repository_get_active_by_customer() -> None:
    repo = InMemoryCartRepository()
    cust_id = uuid4()
    cart = Cart(
        id=uuid4(),
        owner_type=CartOwnerType.CUSTOMER,
        customer_id=cust_id,
        currency="USD",
        status=CartStatus.ACTIVE,
    )
    await repo.save(cart)

    active = await repo.get_active_by_customer(cust_id)
    assert active is not None
    assert active.id == cart.id

    assert await repo.get_active_by_customer(uuid4()) is None

    cart.status = CartStatus.EXPIRED
    await repo.save(cart)
    assert await repo.get_active_by_customer(cust_id) is None


@pytest.mark.asyncio
async def test_cart_line_repository_crud() -> None:
    repo = InMemoryCartLineRepository()
    cart_id = uuid4()
    line_id = uuid4()
    line = CartLine(
        id=line_id,
        cart_id=cart_id,
        product_id=uuid4(),
        listing_id=uuid4(),
        unit_price=Decimal("49.99"),
        currency="USD",
        quantity=2,
    )

    await repo.save(line)

    fetched = await repo.get(line_id)
    assert fetched is not None
    assert fetched.id == line_id
    assert fetched.quantity == 2

    lines = await repo.list_by_cart(cart_id)
    assert len(lines) == 1
    assert lines[0].id == line_id

    # Line from another cart should not be returned
    other_line = CartLine(
        id=uuid4(),
        cart_id=uuid4(),
        product_id=uuid4(),
        listing_id=uuid4(),
        unit_price=Decimal("19.99"),
        currency="USD",
        quantity=1,
    )
    await repo.save(other_line)
    assert len(await repo.list_by_cart(cart_id)) == 1

    # Removed line should not be returned by list_by_cart
    line.status = CartLineStatus.REMOVED
    await repo.save(line)
    assert len(await repo.list_by_cart(cart_id)) == 0

    # Delete
    await repo.delete(line_id)
    assert await repo.get(line_id) is None
