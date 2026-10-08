from uuid import uuid4

import pytest

from fashx.domain.checkout.entities import CheckoutSession
from fashx.repositories.checkout.memory import InMemoryCheckoutRepository


@pytest.mark.asyncio
async def test_in_memory_checkout_repository():
    repo = InMemoryCheckoutRepository()
    cart_id = uuid4()

    session = CheckoutSession(
        cart_id=cart_id,
        customer_id=uuid4(),
    )

    await repo.save(session)

    # Get by ID
    fetched = await repo.get(session.id)
    assert fetched is not None
    assert fetched.id == session.id

    # Get by cart
    by_cart = await repo.get_by_cart(cart_id)
    assert by_cart is not None
    assert by_cart.id == session.id

    # Non-existent
    assert await repo.get(uuid4()) is None
    assert await repo.get_by_cart(uuid4()) is None
