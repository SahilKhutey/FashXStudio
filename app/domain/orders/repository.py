from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from .entities import (
    CheckoutSession,
    Order,
    OrderLine,
)


class CheckoutRepository(ABC):
    @abstractmethod
    async def get(
        self,
        checkout_id: UUID,
    ) -> CheckoutSession | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        checkout: CheckoutSession,
    ) -> CheckoutSession:
        raise NotImplementedError

    @abstractmethod
    async def get_by_idempotency_key(
        self,
        key: str,
    ) -> CheckoutSession | None:
        raise NotImplementedError


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
