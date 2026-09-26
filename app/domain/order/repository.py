from abc import ABC, abstractmethod
from uuid import UUID

from .entities import Order, OrderLine


class OrderRepository(ABC):
    @abstractmethod
    async def get(
        self,
        order_id: UUID,
    ) -> Order | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_number(
        self,
        order_number: str,
    ) -> Order | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        order: Order,
    ) -> Order:
        raise NotImplementedError

    @abstractmethod
    async def list_by_customer(
        self,
        customer_id: UUID,
    ) -> list[Order]:
        raise NotImplementedError


class OrderLineRepository(ABC):
    @abstractmethod
    async def save(
        self,
        line: OrderLine,
    ) -> OrderLine:
        raise NotImplementedError

    @abstractmethod
    async def list_by_order(
        self,
        order_id: UUID,
    ) -> list[OrderLine]:
        raise NotImplementedError
