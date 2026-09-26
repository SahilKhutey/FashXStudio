from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.context import CoreContext
from app.core.errors import NotFoundError, ValidationError
from app.core.event_bus import EventBus
from app.domain.returns.entities import (
    CancellationRequest,
    Refund,
    ReplacementRequest,
    ReturnLine,
    ReturnRequest,
)
from app.domain.returns.enums import (
    CancellationStatus,
    RefundReason,
    RefundStatus,
    ReplacementStatus,
    ReturnReason,
    ReturnStatus,
)
from app.domain.returns.events import (
    CancellationCompleted,
    CancellationRequested,
    RefundCompleted,
    RefundFailed,
    RefundRequested,
    ReplacementRequested,
    ReturnAccepted,
    ReturnRejected,
    ReturnRequested,
)
from app.domain.returns.service import (
    ReturnsService,
)
from app.repositories.returns.memory import (
    InMemoryCancellationRepository,
    InMemoryRefundRepository,
    InMemoryReplacementRepository,
    InMemoryReturnLineRepository,
    InMemoryReturnRepository,
)


def build_service() -> tuple[ReturnsService, list]:
    published_events = []
    bus = EventBus()

    async def handler(envelope):
        published_events.append(envelope.event)

    for event_name in [
        "CancellationRequested",
        "CancellationCompleted",
        "ReturnRequested",
        "ReturnAccepted",
        "ReturnRejected",
        "RefundRequested",
        "RefundCompleted",
        "RefundFailed",
        "ReplacementRequested",
    ]:
        bus.subscribe(event_name, handler)

    service = ReturnsService(
        return_repository=InMemoryReturnRepository(),
        return_line_repository=InMemoryReturnLineRepository(),
        cancellation_repository=InMemoryCancellationRepository(),
        refund_repository=InMemoryRefundRepository(),
        replacement_repository=InMemoryReplacementRepository(),
        event_bus=bus,
    )
    return service, published_events


@pytest.mark.asyncio
async def test_request_return():
    service, events = build_service()
    order_id = uuid4()
    customer_id = uuid4()

    request = ReturnRequest(
        order_id=order_id,
        customer_id=customer_id,
        reason=ReturnReason.DEFECTIVE,
        notes="Item stopped working",
    )
    lines = [
        ReturnLine(
            order_line_id=uuid4(),
            product_id=uuid4(),
            quantity=1,
            refund_amount=Decimal("1200.00"),
        )
    ]

    result = await service.request_return(
        context=CoreContext.create(),
        request=request,
        lines=lines,
    )

    assert result.id is not None
    assert result.status == ReturnStatus.REQUESTED
    assert len(events) == 1
    assert isinstance(events[0], ReturnRequested)
    assert events[0].entity_id == result.id


@pytest.mark.asyncio
async def test_get_return():
    service, _ = build_service()
    request = ReturnRequest(order_id=uuid4(), customer_id=uuid4())
    await service.request_return(
        context=CoreContext.create(),
        request=request,
        lines=[],
    )

    fetched = await service.get_return(request.id)
    assert fetched.id == request.id

    with pytest.raises(NotFoundError, match="Return request was not found"):
        await service.get_return(uuid4())


@pytest.mark.asyncio
async def test_change_return_status_accepted_and_completed():
    service, events = build_service()
    request = await service.request_return(
        context=CoreContext.create(),
        request=ReturnRequest(order_id=uuid4(), customer_id=uuid4()),
        lines=[],
    )

    for status in [
        ReturnStatus.APPROVED,
        ReturnStatus.PICKUP_PENDING,
        ReturnStatus.IN_TRANSIT,
        ReturnStatus.RECEIVED,
        ReturnStatus.INSPECTION,
        ReturnStatus.ACCEPTED,
        ReturnStatus.COMPLETED,
    ]:
        await service.change_return_status(
            context=CoreContext.create(),
            return_id=request.id,
            target=status,
        )

    assert any(isinstance(e, ReturnAccepted) for e in events)

    # Completed is terminal
    with pytest.raises(ValidationError, match="Invalid return transition"):
        await service.change_return_status(
            context=CoreContext.create(),
            return_id=request.id,
            target=ReturnStatus.REJECTED,
        )


@pytest.mark.asyncio
async def test_change_return_status_rejected():
    service, events = build_service()
    request = await service.request_return(
        context=CoreContext.create(),
        request=ReturnRequest(order_id=uuid4(), customer_id=uuid4()),
        lines=[],
    )

    for status in [
        ReturnStatus.APPROVED,
        ReturnStatus.PICKUP_PENDING,
        ReturnStatus.IN_TRANSIT,
        ReturnStatus.RECEIVED,
        ReturnStatus.INSPECTION,
        ReturnStatus.REJECTED,
    ]:
        await service.change_return_status(
            context=CoreContext.create(),
            return_id=request.id,
            target=status,
        )

    assert any(isinstance(e, ReturnRejected) for e in events)


@pytest.mark.asyncio
async def test_request_and_complete_cancellation():
    service, events = build_service()
    order_id = uuid4()
    req = CancellationRequest(
        order_id=order_id,
        customer_id=uuid4(),
        reason="Ordered by mistake",
    )

    created = await service.request_cancellation(
        context=CoreContext.create(),
        request=req,
    )
    assert created.status == CancellationStatus.REQUESTED
    assert any(isinstance(e, CancellationRequested) for e in events)

    approved = await service.change_cancellation_status(
        context=CoreContext.create(),
        cancellation_id=created.id,
        target=CancellationStatus.APPROVED,
    )
    assert approved.status == CancellationStatus.APPROVED

    completed = await service.change_cancellation_status(
        context=CoreContext.create(),
        cancellation_id=created.id,
        target=CancellationStatus.COMPLETED,
    )
    assert completed.status == CancellationStatus.COMPLETED
    assert any(isinstance(e, CancellationCompleted) for e in events)


@pytest.mark.asyncio
async def test_cancellation_not_found():
    service, _ = build_service()
    with pytest.raises(NotFoundError, match="Cancellation was not found"):
        await service.change_cancellation_status(
            context=CoreContext.create(),
            cancellation_id=uuid4(),
            target=CancellationStatus.APPROVED,
        )


@pytest.mark.asyncio
async def test_refund_lifecycle():
    service, events = build_service()
    refund = Refund(
        order_id=uuid4(),
        amount=Decimal("999.00"),
        reason=RefundReason.ORDER_CANCELLED,
    )

    requested = await service.request_refund(
        context=CoreContext.create(),
        refund=refund,
    )
    assert requested.status == RefundStatus.REQUESTED
    assert any(isinstance(e, RefundRequested) for e in events)

    await service.change_refund_status(
        context=CoreContext.create(),
        refund_id=requested.id,
        target=RefundStatus.APPROVED,
    )
    await service.change_refund_status(
        context=CoreContext.create(),
        refund_id=requested.id,
        target=RefundStatus.PROCESSING,
    )
    completed = await service.change_refund_status(
        context=CoreContext.create(),
        refund_id=requested.id,
        target=RefundStatus.COMPLETED,
    )
    assert completed.status == RefundStatus.COMPLETED
    assert any(isinstance(e, RefundCompleted) for e in events)


@pytest.mark.asyncio
async def test_refund_failed_event():
    service, events = build_service()
    refund = await service.request_refund(
        context=CoreContext.create(),
        refund=Refund(order_id=uuid4(), amount=Decimal("150.00")),
    )
    await service.change_refund_status(
        context=CoreContext.create(),
        refund_id=refund.id,
        target=RefundStatus.APPROVED,
    )
    await service.change_refund_status(
        context=CoreContext.create(),
        refund_id=refund.id,
        target=RefundStatus.PROCESSING,
    )
    failed = await service.change_refund_status(
        context=CoreContext.create(),
        refund_id=refund.id,
        target=RefundStatus.FAILED,
    )
    assert failed.status == RefundStatus.FAILED
    assert any(isinstance(e, RefundFailed) for e in events)


@pytest.mark.asyncio
async def test_refund_not_found():
    service, _ = build_service()
    with pytest.raises(NotFoundError, match="Refund was not found"):
        await service.change_refund_status(
            context=CoreContext.create(),
            refund_id=uuid4(),
            target=RefundStatus.APPROVED,
        )


@pytest.mark.asyncio
async def test_request_replacement():
    service, events = build_service()
    replacement = ReplacementRequest(
        order_id=uuid4(),
        original_order_line_id=uuid4(),
        replacement_product_id=uuid4(),
        status=ReplacementStatus.REQUESTED,
    )

    created = await service.request_replacement(
        context=CoreContext.create(),
        replacement=replacement,
    )
    assert created.id is not None
    assert any(isinstance(e, ReplacementRequested) for e in events)
