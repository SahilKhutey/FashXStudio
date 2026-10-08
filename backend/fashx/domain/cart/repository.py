from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from .entities import Cart, CartLine


class CartRepository(ABC):
    @abstractmethod
    async def get(
        self,
        cart_id: UUID,
    ) -> Cart | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        cart: Cart,
    ) -> Cart:
        raise NotImplementedError

    @abstractmethod
    async def get_active_by_customer(
        self,
        customer_id: UUID,
    ) -> Cart | None:
        raise NotImplementedError

    @abstractmethod
    async def get_active_by_session(
        self,
        session_id: str,
    ) -> Cart | None:
        raise NotImplementedError


class CartLineRepository(ABC):
    @abstractmethod
    async def get(
        self,
        line_id: UUID,
    ) -> CartLine | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        line: CartLine,
    ) -> CartLine:
        raise NotImplementedError

    @abstractmethod
    async def delete(
        self,
        line_id: UUID,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_cart(
        self,
        cart_id: UUID,
    ) -> list[CartLine]:
        raise NotImplementedError
