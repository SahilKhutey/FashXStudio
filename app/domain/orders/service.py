from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.core.context import CoreContext
from app.core.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.event_bus import EventBus

from .entities import (
    CheckoutSession,
    Order,
    OrderLine,
)
from .enums import (
    CheckoutStatus,
    OrderStatus,
)
from .events import (
    CheckoutCompleted,
    CheckoutCreated,
    CheckoutValidated,
    OrderCreated,
    OrderStatusChanged,
)
from .lifecycle import validate_order_transition
from .repository import (
    CheckoutRepository,
    OrderLineRepository,
    OrderRepository,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class CheckoutResult:
    checkout: CheckoutSession
    order: Order


class OrderNumberGenerator:
    def __init__(self) -> None:
        self._sequence = 0

    def next(self) -> str:
        self._sequence += 1
        return f"FXS-{self._sequence:08d}"


class CheckoutService:
    def __init__(
        self,
        checkout_repository: CheckoutRepository,
        order_repository: OrderRepository,
        line_repository: OrderLineRepository,
        event_bus: EventBus,
        order_number_generator: OrderNumberGenerator,
    ) -> None:
        self.checkout_repository = checkout_repository
        self.order_repository = order_repository
        self.line_repository = line_repository
        self.event_bus = event_bus
        self.order_number_generator = order_number_generator

    async def create_checkout(
        self,
        *,
        context: CoreContext,
        checkout: CheckoutSession,
    ) -> CheckoutSession:
        checkout.validate()

        if checkout.idempotency_key:
            existing = (
                await self.checkout_repository.get_by_idempotency_key(
                    checkout.idempotency_key
                )
            )
            if existing:
                return existing

        await self.checkout_repository.save(checkout)

        await self.event_bus.publish(
            CheckoutCreated(
                entity_id=checkout.id,
                correlation_id=context.correlation_id,
            )
        )

        return checkout

    async def get_checkout(
        self,
        checkout_id: UUID,
    ) -> CheckoutSession:
        checkout = await self.checkout_repository.get(checkout_id)

        if checkout is None:
            raise NotFoundError(
                "Checkout was not found.",
                {"checkout_id": str(checkout_id)},
            )

        return checkout

    async def validate_checkout(
        self,
        *,
        context: CoreContext,
        checkout_id: UUID,
    ) -> CheckoutSession:
        checkout = await self.get_checkout(checkout_id)

        if checkout.status != CheckoutStatus.CREATED:
            raise ConflictError("Checkout is not in a valid state.")

        checkout.status = CheckoutStatus.VALIDATED
        checkout.updated_at = utc_now()
        checkout.version += 1

        await self.checkout_repository.save(checkout)

        await self.event_bus.publish(
            CheckoutValidated(
                entity_id=checkout.id,
                correlation_id=context.correlation_id,
            )
        )

        return checkout

    async def complete_checkout(
        self,
        *,
        context: CoreContext,
        checkout_id: UUID,
        lines: list[OrderLine],
    ) -> CheckoutResult:
        checkout = await self.get_checkout(checkout_id)

        if checkout.status not in {
            CheckoutStatus.CREATED,
            CheckoutStatus.VALIDATED,
        }:
            raise ConflictError("Checkout cannot be completed.")

        if not lines:
            raise ValidationError(
                "Checkout requires at least one item."
            )

        subtotal = sum(
            (line.subtotal for line in lines),
            Decimal("0"),
        )

        discount = sum(
            (
                line.discount * Decimal(line.quantity)
                for line in lines
            ),
            Decimal("0"),
        )

        total = max(
            subtotal,
            Decimal("0"),
        )

        email = checkout.email
        if not email and checkout.customer_id:
            email = f"customer-{checkout.customer_id}@checkout.local"

        order = Order(
            order_number=self.order_number_generator.next(),
            checkout_id=checkout.id,
            cart_id=checkout.cart_id,
            customer_id=checkout.customer_id,
            email=email,
            currency=checkout.currency,
            subtotal=subtotal,
            discount=discount,
            total=total,
        )

        order.validate()

        for line in lines:
            if line.currency.upper() != checkout.currency.upper():
                raise ValidationError(
                    "Order line currency must match checkout."
                )

            line.order_id = order.id
            line.validate()

            await self.line_repository.save(line)

        await self.order_repository.save(order)

        checkout.status = CheckoutStatus.COMPLETED
        checkout.updated_at = utc_now()
        checkout.version += 1

        await self.checkout_repository.save(checkout)

        await self.event_bus.publish(
            OrderCreated(
                entity_id=order.id,
                correlation_id=context.correlation_id,
            )
        )

        await self.event_bus.publish(
            CheckoutCompleted(
                entity_id=checkout.id,
                correlation_id=context.correlation_id,
            )
        )

        return CheckoutResult(
            checkout=checkout,
            order=order,
        )

    async def change_order_status(
        self,
        *,
        context: CoreContext,
        order_id: UUID,
        target: OrderStatus,
    ) -> Order:
        order = await self.order_repository.get(order_id)

        if order is None:
            raise NotFoundError(
                "Order was not found.",
                {"order_id": str(order_id)},
            )

        validate_order_transition(
            order.status,
            target,
        )

        order.status = target
        order.touch()

        await self.order_repository.save(order)

        await self.event_bus.publish(
            OrderStatusChanged(
                entity_id=order.id,
                correlation_id=context.correlation_id,
            )
        )

        return order
