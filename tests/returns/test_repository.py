from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.returns.entities import (
    CancellationRequest,
    Refund,
    ReplacementRequest,
    ReturnLine,
    ReturnRequest,
)
from fashx.repositories.returns.memory import (
    InMemoryCancellationRepository,
    InMemoryRefundRepository,
    InMemoryReplacementRepository,
    InMemoryReturnLineRepository,
    InMemoryReturnRepository,
)


@pytest.mark.asyncio
async def test_return_repositories():
    ret_repo = InMemoryReturnRepository()
    line_repo = InMemoryReturnLineRepository()

    order_id = uuid4()
    customer_id = uuid4()
    req = ReturnRequest(order_id=order_id, customer_id=customer_id)

    await ret_repo.save(req)
    fetched = await ret_repo.get(req.id)
    assert fetched is not None
    assert fetched.id == req.id

    assert await ret_repo.get(uuid4()) is None

    by_order = await ret_repo.list_by_order(order_id)
    assert len(by_order) == 1
    assert by_order[0].id == req.id

    line1 = ReturnLine(
        return_id=req.id,
        order_line_id=uuid4(),
        product_id=uuid4(),
        quantity=1,
    )
    line2 = ReturnLine(
        return_id=req.id,
        order_line_id=uuid4(),
        product_id=uuid4(),
        quantity=2,
    )
    await line_repo.save(line1)
    await line_repo.save(line2)

    lines = await line_repo.list_by_return(req.id)
    assert len(lines) == 2
    assert {line.id for line in lines} == {line1.id, line2.id}


@pytest.mark.asyncio
async def test_cancellation_repository():
    repo = InMemoryCancellationRepository()
    order_id = uuid4()
    cancellation = CancellationRequest(
        order_id=order_id,
        customer_id=uuid4(),
        reason="Mistake order",
    )

    await repo.save(cancellation)
    assert await repo.get(cancellation.id) == cancellation
    assert await repo.get_by_order(order_id) == cancellation
    assert await repo.get_by_order(uuid4()) is None
    assert await repo.get(uuid4()) is None


@pytest.mark.asyncio
async def test_refund_repository():
    repo = InMemoryRefundRepository()
    order_id = uuid4()
    refund1 = Refund(order_id=order_id, amount=Decimal("250.00"))
    refund2 = Refund(order_id=order_id, amount=Decimal("150.00"))

    await repo.save(refund1)
    await repo.save(refund2)

    assert await repo.get(refund1.id) == refund1
    assert await repo.get(uuid4()) is None

    refunds = await repo.list_by_order(order_id)
    assert len(refunds) == 2


@pytest.mark.asyncio
async def test_replacement_repository():
    repo = InMemoryReplacementRepository()
    rep = ReplacementRequest(
        order_id=uuid4(),
        original_order_line_id=uuid4(),
        replacement_product_id=uuid4(),
    )
    await repo.save(rep)
    assert await repo.get(rep.id) == rep
    assert await repo.get(uuid4()) is None
