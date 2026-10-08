from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fashx.core.context import CoreContext
from fashx.core.errors import (
    ConflictError,
    NotFoundError,
)
from fashx.core.event_bus import EventBus

from .entities import (
    Payment,
    PaymentTransaction,
)
from .enums import (
    PaymentStatus,
    TransactionStatus,
    TransactionType,
)
from .events import (
    PaymentAuthorized,
    PaymentCancelled,
    PaymentCaptured,
    PaymentCreated,
    PaymentFailed,
)
from .lifecycle import (
    validate_payment_transition,
)
from .provider import PaymentProvider
from .repository import (
    PaymentRepository,
    PaymentTransactionRepository,
)


@dataclass(slots=True)
class PaymentService:
    payment_repository: PaymentRepository
    transaction_repository: PaymentTransactionRepository
    event_bus: EventBus
    provider: PaymentProvider

    async def create_payment(
        self,
        *,
        context: CoreContext,
        payment: Payment,
    ) -> Payment:
        payment.validate()

        if payment.idempotency_key:
            existing = (
                await self.payment_repository.get_by_idempotency_key(
                    payment.idempotency_key
                )
            )
            if existing:
                return existing

        await self.payment_repository.save(payment)

        await self.event_bus.publish(
            PaymentCreated(
                entity_id=payment.id,
                correlation_id=context.correlation_id,
            )
        )

        return payment

    async def get_payment(
        self,
        payment_id: UUID,
    ) -> Payment:
        payment = await self.payment_repository.get(payment_id)

        if payment is None:
            raise NotFoundError(
                "Payment was not found.",
                {"payment_id": str(payment_id)},
            )

        return payment

    async def authorize(
        self,
        *,
        context: CoreContext,
        payment_id: UUID,
        payment_method: str,
    ) -> Payment:
        payment = await self.get_payment(payment_id)

        if payment.status not in {
            PaymentStatus.CREATED,
            PaymentStatus.REQUIRES_ACTION,
        }:
            raise ConflictError(
                "Payment cannot be authorized."
            )

        result = await self.provider.authorize(
            amount=payment.amount,
            currency=payment.currency,
            payment_method=payment_method,
            metadata=payment.metadata,
        )

        if result.requires_action:
            payment.status = PaymentStatus.REQUIRES_ACTION
            payment.touch()
            await self.payment_repository.save(payment)
            return payment

        if not result.success:
            payment.status = PaymentStatus.FAILED
            payment.touch()
            await self.payment_repository.save(payment)
            await self.event_bus.publish(
                PaymentFailed(
                    entity_id=payment.id,
                    correlation_id=context.correlation_id,
                )
            )
            return payment

        payment.status = PaymentStatus.AUTHORIZED
        payment.provider_payment_id = result.provider_payment_id
        payment.touch()

        transaction = PaymentTransaction(
            payment_id=payment.id,
            transaction_type=TransactionType.AUTHORIZATION,
            amount=payment.amount,
            currency=payment.currency,
            status=TransactionStatus.SUCCESS,
            provider_transaction_id=result.provider_transaction_id,
        )
        transaction.validate()

        await self.transaction_repository.save(transaction)
        await self.payment_repository.save(payment)

        await self.event_bus.publish(
            PaymentAuthorized(
                entity_id=payment.id,
                correlation_id=context.correlation_id,
            )
        )

        return payment

    async def capture(
        self,
        *,
        context: CoreContext,
        payment_id: UUID,
    ) -> Payment:
        payment = await self.get_payment(payment_id)

        if payment.status != PaymentStatus.AUTHORIZED:
            raise ConflictError(
                "Only authorized payments can be captured."
            )

        if not payment.provider_payment_id:
            raise ConflictError(
                "Payment has no provider ID."
            )

        result = await self.provider.capture(
            provider_payment_id=payment.provider_payment_id,
            amount=payment.amount,
            currency=payment.currency,
        )

        if not result.success:
            payment.status = PaymentStatus.FAILED
            payment.touch()
            await self.payment_repository.save(payment)
            await self.event_bus.publish(
                PaymentFailed(
                    entity_id=payment.id,
                    correlation_id=context.correlation_id,
                )
            )
            return payment

        payment.status = PaymentStatus.CAPTURED
        payment.touch()

        transaction = PaymentTransaction(
            payment_id=payment.id,
            transaction_type=TransactionType.CAPTURE,
            amount=payment.amount,
            currency=payment.currency,
            status=TransactionStatus.SUCCESS,
            provider_transaction_id=result.provider_transaction_id,
        )
        transaction.validate()

        await self.transaction_repository.save(transaction)
        await self.payment_repository.save(payment)

        await self.event_bus.publish(
            PaymentCaptured(
                entity_id=payment.id,
                correlation_id=context.correlation_id,
            )
        )

        return payment

    async def cancel(
        self,
        *,
        context: CoreContext,
        payment_id: UUID,
    ) -> Payment:
        payment = await self.get_payment(payment_id)

        validate_payment_transition(
            payment.status,
            PaymentStatus.CANCELLED,
        )

        if payment.provider_payment_id:
            await self.provider.cancel(
                provider_payment_id=payment.provider_payment_id
            )

        payment.status = PaymentStatus.CANCELLED
        payment.touch()

        await self.payment_repository.save(payment)

        await self.event_bus.publish(
            PaymentCancelled(
                entity_id=payment.id,
                correlation_id=context.correlation_id,
            )
        )

        return payment
