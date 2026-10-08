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
    Order,
    OrderLine,
)
from .enums import OrderStatus
from .events import (
    OrderCancelled,
    OrderCompleted,
    OrderCreated,
    OrderStatusChanged,
)
from .lifecycle import validate_transition
from .repository import (
    OrderLineRepository,
    OrderRepository,
)


@dataclass(slots=True)
class OrderService:
    order_repository: OrderRepository
    line_repository: OrderLineRepository
    event_bus: EventBus

    async def create_order(
        self,
        *,
        context: CoreContext,
        order: Order,
        lines: list[OrderLine],
    ) -> Order:
        if not lines:
            raise ConflictError("Order must contain at least one line.")

        order.validate()

        for line in lines:
            line.order_id = order.id
            line.validate()
            if line.currency.upper() != order.currency.upper():
                raise ConflictError("Order line currency mismatch.")

        order.calculate_totals(lines)

        existing = await self.order_repository.get_by_number(order.order_number)
        if existing:
            return existing

        await self.order_repository.save(order)

        for line in lines:
            await self.line_repository.save(line)

        await self.event_bus.publish(
            OrderCreated(
                entity_id=order.id,
                correlation_id=context.correlation_id,
            )
        )

        return order

    async def get_order(
        self,
        order_id: UUID,
    ) -> Order:
        order = await self.order_repository.get(order_id)
        if order is None:
            raise NotFoundError("Order not found.")
        return order

    async def change_status(
        self,
        *,
        context: CoreContext,
        order_id: UUID,
        target: OrderStatus,
    ) -> Order:
        order = await self.get_order(order_id)
        validate_transition(order.status, target)
        order.status = target
        order.version += 1
        await self.order_repository.save(order)

        await self.event_bus.publish(
            OrderStatusChanged(
                entity_id=order.id,
                correlation_id=context.correlation_id,
            )
        )

        if target == OrderStatus.CANCELLED or target.value == "cancelled":
            await self.event_bus.publish(
                OrderCancelled(
                    entity_id=order.id,
                    correlation_id=context.correlation_id,
                )
            )

        if target == OrderStatus.COMPLETED or target.value == "completed":
            await self.event_bus.publish(
                OrderCompleted(
                    entity_id=order.id,
                    correlation_id=context.correlation_id,
                )
            )

        return order
