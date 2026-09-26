from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from .entities import (
    Payment,
    PaymentTransaction,
)


class PaymentRepository(ABC):
    @abstractmethod
    async def get(
        self,
        payment_id: UUID,
    ) -> Payment | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_idempotency_key(
        self,
        key: str,
    ) -> Payment | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_order(
        self,
        order_id: UUID,
    ) -> list[Payment]:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        payment: Payment,
    ) -> Payment:
        raise NotImplementedError


class PaymentTransactionRepository(ABC):
    @abstractmethod
    async def save(
        self,
        transaction: PaymentTransaction,
    ) -> PaymentTransaction:
        raise NotImplementedError

    @abstractmethod
    async def list_by_payment(
        self,
        payment_id: UUID,
    ) -> list[PaymentTransaction]:
        raise NotImplementedError
