from __future__ import annotations

from uuid import UUID

from app.domain.cart.entities import (
    Cart,
    CartLine,
)
from app.domain.cart.repository import (
    CartLineRepository,
    CartRepository,
)


class InMemoryCartRepository(CartRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, Cart] = {}

    async def get(
        self,
        cart_id: UUID,
    ) -> Cart | None:
        return self._items.get(cart_id)

    async def save(
        self,
        cart: Cart,
    ) -> Cart:
        self._items[cart.id] = cart
        return cart

    async def get_active_by_customer(
        self,
        customer_id: UUID,
    ) -> Cart | None:
        matches = [
            cart
            for cart in self._items.values()
            if (
                cart.customer_id == customer_id
                and cart.status.value == "active"
            )
        ]
        return matches[0] if matches else None

    async def get_active_by_session(
        self,
        session_id: str,
    ) -> Cart | None:
        matches = [
            cart
            for cart in self._items.values()
            if (
                cart.session_id == session_id
                and cart.status.value == "active"
            )
        ]
        return matches[0] if matches else None


class InMemoryCartLineRepository(CartLineRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, CartLine] = {}

    async def get(
        self,
        line_id: UUID,
    ) -> CartLine | None:
        return self._items.get(line_id)

    async def save(
        self,
        line: CartLine,
    ) -> CartLine:
        self._items[line.id] = line
        return line

    async def delete(
        self,
        line_id: UUID,
    ) -> None:
        self._items.pop(line_id, None)

    async def list_by_cart(
        self,
        cart_id: UUID,
    ) -> list[CartLine]:
        return [
            line
            for line in self._items.values()
            if (
                line.cart_id == cart_id
                and line.status.value == "active"
            )
        ]
