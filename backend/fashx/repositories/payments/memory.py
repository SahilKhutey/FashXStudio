from __future__ import annotations

from uuid import UUID

from fashx.domain.payments.entities import (
    Payment,
    PaymentTransaction,
)
from fashx.domain.payments.repository import (
    PaymentRepository,
    PaymentTransactionRepository,
)


class InMemoryPaymentRepository(PaymentRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, Payment] = {}
        self._idempotency: dict[str, UUID] = {}

    async def get(
        self,
        payment_id: UUID,
    ) -> Payment | None:
        return self._items.get(payment_id)

    async def get_by_idempotency_key(
        self,
        key: str,
    ) -> Payment | None:
        payment_id = self._idempotency.get(key)
        if payment_id is None:
            return None
        return self._items.get(payment_id)

    async def list_by_order(
        self,
        order_id: UUID,
    ) -> list[Payment]:
        return [
            payment
            for payment in self._items.values()
            if payment.order_id == order_id
        ]

    async def save(
        self,
        payment: Payment,
    ) -> Payment:
        self._items[payment.id] = payment
        if payment.idempotency_key:
            self._idempotency[payment.idempotency_key] = payment.id
        return payment


class InMemoryPaymentTransactionRepository(
    PaymentTransactionRepository
):
    def __init__(self) -> None:
        self._items: dict[UUID, PaymentTransaction] = {}

    async def save(
        self,
        transaction: PaymentTransaction,
    ) -> PaymentTransaction:
        self._items[transaction.id] = transaction
        return transaction

    async def list_by_payment(
        self,
        payment_id: UUID,
    ) -> list[PaymentTransaction]:
        return [
            transaction
            for transaction in self._items.values()
            if transaction.payment_id == payment_id
        ]
