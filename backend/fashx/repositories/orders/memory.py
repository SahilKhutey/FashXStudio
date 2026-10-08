from __future__ import annotations

from uuid import UUID

from app.domain.orders.entities import (
    CheckoutSession,
    Order,
    OrderLine,
)
from app.domain.orders.repository import (
    CheckoutRepository,
    OrderLineRepository,
    OrderRepository,
)


class InMemoryCheckoutRepository(CheckoutRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, CheckoutSession] = {}
        self._idempotency: dict[str, UUID] = {}

    async def get(
        self,
        checkout_id: UUID,
    ) -> CheckoutSession | None:
        return self._items.get(checkout_id)

    async def save(
        self,
        checkout: CheckoutSession,
    ) -> CheckoutSession:
        self._items[checkout.id] = checkout
        if checkout.idempotency_key:
            self._idempotency[checkout.idempotency_key] = checkout.id
        return checkout

    async def get_by_idempotency_key(
        self,
        key: str,
    ) -> CheckoutSession | None:
        checkout_id = self._idempotency.get(key)
        if checkout_id is None:
            return None
        return self._items.get(checkout_id)


class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, Order] = {}
        self._numbers: dict[str, UUID] = {}

    async def get(
        self,
        order_id: UUID,
    ) -> Order | None:
        return self._items.get(order_id)

    async def get_by_number(
        self,
        order_number: str,
    ) -> Order | None:
        order_id = self._numbers.get(order_number)
        if order_id is None:
            return None
        return self._items.get(order_id)

    async def save(
        self,
        order: Order,
    ) -> Order:
        self._items[order.id] = order
        self._numbers[order.order_number] = order.id
        return order


class InMemoryOrderLineRepository(OrderLineRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, OrderLine] = {}

    async def save(
        self,
        line: OrderLine,
    ) -> OrderLine:
        self._items[line.id] = line
        return line

    async def list_by_order(
        self,
        order_id: UUID,
    ) -> list[OrderLine]:
        return [
            line
            for line in self._items.values()
            if line.order_id == order_id
        ]
