from uuid import UUID

from fashx.domain.order.entities import (
    Order,
    OrderLine,
)
from fashx.domain.order.repository import (
    OrderLineRepository,
    OrderRepository,
)


class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, Order] = {}
        self._numbers: dict[str, UUID] = {}

    async def get(self, order_id: UUID) -> Order | None:
        return self._items.get(order_id)

    async def get_by_number(self, order_number: str) -> Order | None:
        order_id = self._numbers.get(order_number)
        if order_id is None:
            return None
        return self._items.get(order_id)

    async def save(self, order: Order) -> Order:
        self._items[order.id] = order
        self._numbers[order.order_number] = order.id
        return order

    async def list_by_customer(self, customer_id: UUID) -> list[Order]:
        return [
            order
            for order in self._items.values()
            if order.customer_id == customer_id
        ]


class InMemoryOrderLineRepository(OrderLineRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, OrderLine] = {}

    async def save(self, line: OrderLine) -> OrderLine:
        self._items[line.id] = line
        return line

    async def list_by_order(self, order_id: UUID) -> list[OrderLine]:
        return [
            line
            for line in self._items.values()
            if line.order_id == order_id
        ]
