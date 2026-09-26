from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.context import CoreContext
from app.core.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.event_bus import EventBus
from app.domain.payments.entities import Payment
from app.domain.payments.enums import PaymentStatus
from app.domain.payments.provider import (
    PaymentProvider,
    ProviderPaymentResult,
    TestPaymentProvider,
)
from app.domain.payments.service import (
    PaymentService,
)
from app.repositories.payments.memory import (
    InMemoryPaymentRepository,
    InMemoryPaymentTransactionRepository,
)


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def service(event_bus: EventBus) -> PaymentService:
    return PaymentService(
        payment_repository=InMemoryPaymentRepository(),
        transaction_repository=InMemoryPaymentTransactionRepository(),
        event_bus=event_bus,
        provider=TestPaymentProvider(),
    )


@pytest.mark.asyncio
async def test_create_payment(
    service: PaymentService, event_bus: EventBus
) -> None:
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("PaymentCreated", handler)

    payment = Payment(
        order_id=uuid4(),
        amount=Decimal("1500"),
        currency="INR",
    )
    result = await service.create_payment(
        context=CoreContext.create(),
        payment=payment,
    )

    assert result.status == PaymentStatus.CREATED
    assert len(events) == 1
    assert events[0].entity_id == result.id


@pytest.mark.asyncio
async def test_payment_idempotency(
    service: PaymentService, event_bus: EventBus
) -> None:
    events = []

    async def handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("PaymentCreated", handler)

    order_id = uuid4()
    key = "pay-idem-001"

    first = await service.create_payment(
        context=CoreContext.create(),
        payment=Payment(
            order_id=order_id,
            amount=Decimal("1000"),
            idempotency_key=key,
        ),
    )

    second = await service.create_payment(
        context=CoreContext.create(),
        payment=Payment(
            order_id=order_id,
            amount=Decimal("5000"),
            idempotency_key=key,
        ),
    )

    assert first.id == second.id
    assert second.amount == Decimal("1000")
    assert len(events) == 1


@pytest.mark.asyncio
async def test_get_payment(service: PaymentService) -> None:
    payment = await service.create_payment(
        context=CoreContext.create(),
        payment=Payment(
            order_id=uuid4(),
            amount=Decimal("200"),
        ),
    )

    fetched = await service.get_payment(payment.id)
    assert fetched.id == payment.id

    with pytest.raises(NotFoundError):
        await service.get_payment(uuid4())


@pytest.mark.asyncio
async def test_payment_authorize_and_capture(
    service: PaymentService, event_bus: EventBus
) -> None:
    events_auth = []
    events_capture = []

    async def auth_handler(envelope):
        events_auth.append(envelope.event)

    async def cap_handler(envelope):
        events_capture.append(envelope.event)

    event_bus.subscribe("PaymentAuthorized", auth_handler)
    event_bus.subscribe("PaymentCaptured", cap_handler)

    payment = await service.create_payment(
        context=CoreContext.create(),
        payment=Payment(
            order_id=uuid4(),
            amount=Decimal("1500"),
            currency="INR",
        ),
    )

    payment = await service.authorize(
        context=CoreContext.create(),
        payment_id=payment.id,
        payment_method="upi",
    )
    assert payment.status == PaymentStatus.AUTHORIZED
    assert len(events_auth) == 1
    assert events_auth[0].entity_id == payment.id

    txns = await service.transaction_repository.list_by_payment(payment.id)
    assert len(txns) == 1
    assert txns[0].transaction_type.value == "authorization"

    payment = await service.capture(
        context=CoreContext.create(),
        payment_id=payment.id,
    )
    assert payment.status == PaymentStatus.CAPTURED
    assert len(events_capture) == 1
    assert events_capture[0].entity_id == payment.id

    txns_after = await service.transaction_repository.list_by_payment(payment.id)
    assert len(txns_after) == 2


@pytest.mark.asyncio
async def test_payment_authorize_requires_action(
    event_bus: EventBus,
) -> None:
    class RequiresActionProvider(PaymentProvider):
        async def authorize(
            self, *, amount, currency, payment_method, metadata
        ):
            return ProviderPaymentResult(
                success=False,
                requires_action=True,
            )

        async def capture(self, *, provider_payment_id, amount, currency):
            raise NotImplementedError

        async def cancel(self, *, provider_payment_id):
            raise NotImplementedError

    service = PaymentService(
        payment_repository=InMemoryPaymentRepository(),
        transaction_repository=InMemoryPaymentTransactionRepository(),
        event_bus=event_bus,
        provider=RequiresActionProvider(),
    )

    payment = await service.create_payment(
        context=CoreContext.create(),
        payment=Payment(
            order_id=uuid4(),
            amount=Decimal("500"),
        ),
    )

    auth_payment = await service.authorize(
        context=CoreContext.create(),
        payment_id=payment.id,
        payment_method="card",
    )
    assert auth_payment.status == PaymentStatus.REQUIRES_ACTION


@pytest.mark.asyncio
async def test_payment_authorize_failure(
    event_bus: EventBus,
) -> None:
    events = []

    async def fail_handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("PaymentFailed", fail_handler)

    class FailingProvider(PaymentProvider):
        async def authorize(
            self, *, amount, currency, payment_method, metadata
        ):
            return ProviderPaymentResult(
                success=False,
                error_code="INSUFFICIENT_FUNDS",
                error_message="Card declined.",
            )

        async def capture(self, *, provider_payment_id, amount, currency):
            raise NotImplementedError

        async def cancel(self, *, provider_payment_id):
            raise NotImplementedError

    service = PaymentService(
        payment_repository=InMemoryPaymentRepository(),
        transaction_repository=InMemoryPaymentTransactionRepository(),
        event_bus=event_bus,
        provider=FailingProvider(),
    )

    payment = await service.create_payment(
        context=CoreContext.create(),
        payment=Payment(
            order_id=uuid4(),
            amount=Decimal("500"),
        ),
    )

    auth_payment = await service.authorize(
        context=CoreContext.create(),
        payment_id=payment.id,
        payment_method="card",
    )
    assert auth_payment.status == PaymentStatus.FAILED
    assert len(events) == 1
    assert events[0].entity_id == payment.id


@pytest.mark.asyncio
async def test_payment_capture_failures(
    event_bus: EventBus,
) -> None:
    # 1. Capture on non-authorized payment raises ConflictError
    service = PaymentService(
        payment_repository=InMemoryPaymentRepository(),
        transaction_repository=InMemoryPaymentTransactionRepository(),
        event_bus=event_bus,
        provider=TestPaymentProvider(),
    )
    payment = await service.create_payment(
        context=CoreContext.create(),
        payment=Payment(order_id=uuid4(), amount=Decimal("100")),
    )
    with pytest.raises(
        ConflictError, match="Only authorized payments can be captured"
    ):
        await service.capture(
            context=CoreContext.create(),
            payment_id=payment.id,
        )

    # 2. Provider capture failure marks payment as FAILED
    class CaptureFailingProvider(TestPaymentProvider):
        async def capture(self, *, provider_payment_id, amount, currency):
            return ProviderPaymentResult(
                success=False,
                error_code="CAPTURE_FAILED",
            )

    service2 = PaymentService(
        payment_repository=InMemoryPaymentRepository(),
        transaction_repository=InMemoryPaymentTransactionRepository(),
        event_bus=event_bus,
        provider=CaptureFailingProvider(),
    )
    payment2 = await service2.create_payment(
        context=CoreContext.create(),
        payment=Payment(order_id=uuid4(), amount=Decimal("100")),
    )
    await service2.authorize(
        context=CoreContext.create(),
        payment_id=payment2.id,
        payment_method="upi",
    )
    failed_capture = await service2.capture(
        context=CoreContext.create(),
        payment_id=payment2.id,
    )
    assert failed_capture.status == PaymentStatus.FAILED


@pytest.mark.asyncio
async def test_payment_cancel(
    service: PaymentService, event_bus: EventBus
) -> None:
    events = []

    async def cancel_handler(envelope):
        events.append(envelope.event)

    event_bus.subscribe("PaymentCancelled", cancel_handler)

    payment = await service.create_payment(
        context=CoreContext.create(),
        payment=Payment(order_id=uuid4(), amount=Decimal("750")),
    )
    cancelled = await service.cancel(
        context=CoreContext.create(),
        payment_id=payment.id,
    )
    assert cancelled.status == PaymentStatus.CANCELLED
    assert len(events) == 1

    # Cancelling already cancelled payment raises ValidationError
    with pytest.raises(ValidationError):
        await service.cancel(
            context=CoreContext.create(),
            payment_id=payment.id,
        )
