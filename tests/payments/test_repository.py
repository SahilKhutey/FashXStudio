from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from fashx.domain.payments.entities import (
    Payment,
    PaymentTransaction,
)
from fashx.domain.payments.enums import TransactionType
from fashx.repositories.payments.memory import (
    InMemoryPaymentRepository,
    InMemoryPaymentTransactionRepository,
)


@pytest.mark.asyncio
async def test_payment_repository_crud() -> None:
    repo = InMemoryPaymentRepository()
    order_id = uuid4()
    payment = Payment(
        order_id=order_id,
        amount=Decimal("1200"),
        idempotency_key="pay-key-1",
    )
    await repo.save(payment)

    fetched = await repo.get(payment.id)
    assert fetched is not None
    assert fetched.id == payment.id

    by_key = await repo.get_by_idempotency_key("pay-key-1")
    assert by_key is not None
    assert by_key.id == payment.id

    by_order = await repo.list_by_order(order_id)
    assert len(by_order) == 1
    assert by_order[0].id == payment.id

    assert await repo.get(uuid4()) is None
    assert await repo.get_by_idempotency_key("non-existent") is None
    assert len(await repo.list_by_order(uuid4())) == 0


@pytest.mark.asyncio
async def test_payment_transaction_repository_crud() -> None:
    repo = InMemoryPaymentTransactionRepository()
    payment_id1 = uuid4()
    payment_id2 = uuid4()

    tx1 = PaymentTransaction(
        payment_id=payment_id1,
        transaction_type=TransactionType.AUTHORIZATION,
        amount=Decimal("500"),
    )
    tx2 = PaymentTransaction(
        payment_id=payment_id1,
        transaction_type=TransactionType.CAPTURE,
        amount=Decimal("500"),
    )
    tx3 = PaymentTransaction(
        payment_id=payment_id2,
        transaction_type=TransactionType.AUTHORIZATION,
        amount=Decimal("100"),
    )

    await repo.save(tx1)
    await repo.save(tx2)
    await repo.save(tx3)

    list1 = await repo.list_by_payment(payment_id1)
    assert len(list1) == 2
    assert {txn.id for txn in list1} == {tx1.id, tx2.id}

    list2 = await repo.list_by_payment(payment_id2)
    assert len(list2) == 1
    assert list2[0].id == tx3.id

    assert len(await repo.list_by_payment(uuid4())) == 0
