from abc import ABC, abstractmethod
from uuid import UUID

from .entities import CheckoutSession


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
    async def get_by_cart(
        self,
        cart_id: UUID,
    ) -> CheckoutSession | None:
        raise NotImplementedError
