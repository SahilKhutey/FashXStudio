from uuid import UUID

from fashx.domain.checkout.entities import (
    CheckoutSession,
)
from fashx.domain.checkout.repository import (
    CheckoutRepository,
)


class InMemoryCheckoutRepository(CheckoutRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, CheckoutSession] = {}
        self._cart_index: dict[UUID, UUID] = {}

    async def get(self, checkout_id: UUID) -> CheckoutSession | None:
        return self._items.get(checkout_id)

    async def save(self, checkout: CheckoutSession) -> CheckoutSession:
        self._items[checkout.id] = checkout
        if checkout.cart_id:
            self._cart_index[checkout.cart_id] = checkout.id
        return checkout

    async def get_by_cart(self, cart_id: UUID) -> CheckoutSession | None:
        checkout_id = self._cart_index.get(cart_id)
        if checkout_id is None:
            return None
        return self._items.get(checkout_id)
