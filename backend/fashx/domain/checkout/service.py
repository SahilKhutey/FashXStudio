from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fashx.core.context import CoreContext
from fashx.core.errors import (
    ConflictError,
    NotFoundError,
)
from fashx.core.event_bus import EventBus

from .entities import CheckoutSession
from .enums import CheckoutStatus
from .events import (
    CheckoutCreated,
    CheckoutValidated,
)
from .lifecycle import validate_transition
from .repository import CheckoutRepository


@dataclass(slots=True)
class CheckoutService:
    checkout_repository: CheckoutRepository
    event_bus: EventBus
    order_service: object = None
    cart_repository: object = None
    cart_line_repository: object = None

    @property
    def order_repository(self) -> object:
        if self.order_service is not None:
            return getattr(self.order_service, "order_repository", None)
        return None

    @property
    def line_repository(self) -> object:
        if self.order_service is not None:
            return getattr(self.order_service, "line_repository", None)
        return None

    async def create_checkout(
        self,
        *,
        context: CoreContext,
        checkout: CheckoutSession,
    ) -> CheckoutSession:
        checkout.validate()

        if checkout.cart_id:
            existing = await self.checkout_repository.get_by_cart(
                checkout.cart_id
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
            raise NotFoundError("Checkout not found.")
        return checkout

    async def validate_checkout(
        self,
        *,
        context: CoreContext,
        checkout_id: UUID,
    ) -> CheckoutSession:
        checkout = await self.get_checkout(checkout_id)

        validate_transition(
            checkout.status,
            CheckoutStatus.VALIDATING,
        )

        checkout.status = CheckoutStatus.READY
        checkout.version += 1

        await self.checkout_repository.save(checkout)

        await self.event_bus.publish(
            CheckoutValidated(
                entity_id=checkout.id,
                correlation_id=context.correlation_id,
            )
        )

        return checkout

    async def convert_to_order(
        self,
        *,
        context: CoreContext,
        checkout_id: UUID,
        order: object,
        lines: list[object],
    ) -> object:
        checkout = await self.get_checkout(checkout_id)

        if checkout.status != CheckoutStatus.READY and checkout.status.value != "ready":
            raise ConflictError("Checkout is not ready.")

        if self.order_service is None:
            raise ConflictError("Order service is not configured.")

        created_order = await self.order_service.create_order(
            context=context,
            order=order,
            lines=lines,
        )

        checkout.order_id = created_order.id
        checkout.status = CheckoutStatus.PAYMENT_PENDING
        checkout.version += 1

        await self.checkout_repository.save(checkout)

        return created_order
