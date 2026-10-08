from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from fashx.core.context import CoreContext
from fashx.core.errors import NotFoundError, ValidationError
from fashx.core.event_bus import EventBus

from .entities import Cart, CartLine
from .enums import CartLineStatus, CartStatus
from .events import (
    CartCleared,
    CartCreated,
    CartLineAdded,
    CartLineQuantityChanged,
    CartLineRemoved,
    CartStatusChanged,
)
from .lifecycle import validate_cart_transition
from .repository import (
    CartLineRepository,
    CartRepository,
)


@dataclass(frozen=True, slots=True)
class CartTotals:
    subtotal: Decimal
    item_count: int
    currency: str


class CartService:
    def __init__(
        self,
        cart_repository: CartRepository,
        line_repository: CartLineRepository,
        event_bus: EventBus,
    ) -> None:
        self.cart_repository = cart_repository
        self.line_repository = line_repository
        self.event_bus = event_bus

    async def create_cart(
        self,
        *,
        context: CoreContext,
        cart: Cart,
    ) -> Cart:
        cart.validate()

        existing = None

        if cart.customer_id:
            existing = (
                await self.cart_repository.get_active_by_customer(
                    cart.customer_id
                )
            )
        elif cart.session_id:
            existing = (
                await self.cart_repository.get_active_by_session(
                    cart.session_id
                )
            )

        if existing is not None:
            return existing

        await self.cart_repository.save(cart)

        await self.event_bus.publish(
            CartCreated(
                entity_id=cart.id,
                correlation_id=context.correlation_id,
            )
        )

        return cart

    async def get_cart(
        self,
        cart_id: UUID,
    ) -> Cart:
        cart = await self.cart_repository.get(cart_id)

        if cart is None:
            raise NotFoundError(
                "Cart was not found.",
                {"cart_id": str(cart_id)},
            )

        return cart

    async def add_line(
        self,
        *,
        context: CoreContext,
        cart_id: UUID,
        line: CartLine,
    ) -> CartLine:
        cart = await self.get_cart(cart_id)

        if cart.status != CartStatus.ACTIVE:
            raise ValidationError(
                "Items can only be added to an active cart."
            )

        if cart.is_expired():
            raise ValidationError(
                "Expired cart cannot receive items."
            )

        if line.cart_id != cart.id:
            raise ValidationError(
                "Cart line does not belong to cart."
            )

        line.validate()

        if line.currency.upper() != cart.currency.upper():
            raise ValidationError(
                "Cart line currency must match cart currency."
            )

        existing_lines = await self.line_repository.list_by_cart(cart.id)

        for existing in existing_lines:
            if (
                existing.product_id == line.product_id
                and existing.variant_id == line.variant_id
                and existing.listing_id == line.listing_id
            ):
                existing.quantity += line.quantity
                existing.updated_at = line.updated_at

                await self.line_repository.save(existing)

                cart.touch()
                await self.cart_repository.save(cart)

                await self.event_bus.publish(
                    CartLineQuantityChanged(
                        entity_id=existing.id,
                        correlation_id=context.correlation_id,
                    )
                )

                return existing

        await self.line_repository.save(line)

        cart.touch()
        await self.cart_repository.save(cart)

        await self.event_bus.publish(
            CartLineAdded(
                entity_id=line.id,
                correlation_id=context.correlation_id,
            )
        )

        return line

    async def update_quantity(
        self,
        *,
        context: CoreContext,
        line_id: UUID,
        quantity: int,
    ) -> CartLine:
        line = await self.line_repository.get(line_id)

        if line is None:
            raise NotFoundError(
                "Cart line was not found.",
                {"line_id": str(line_id)},
            )

        line.update_quantity(quantity)

        await self.line_repository.save(line)

        await self.event_bus.publish(
            CartLineQuantityChanged(
                entity_id=line.id,
                correlation_id=context.correlation_id,
            )
        )

        return line

    async def remove_line(
        self,
        *,
        context: CoreContext,
        line_id: UUID,
    ) -> CartLine:
        line = await self.line_repository.get(line_id)

        if line is None:
            raise NotFoundError(
                "Cart line was not found.",
                {"line_id": str(line_id)},
            )

        line.remove()

        await self.line_repository.save(line)

        await self.event_bus.publish(
            CartLineRemoved(
                entity_id=line.id,
                correlation_id=context.correlation_id,
            )
        )

        return line

    async def clear_cart(
        self,
        *,
        context: CoreContext,
        cart_id: UUID,
    ) -> None:
        cart = await self.get_cart(cart_id)

        lines = await self.line_repository.list_by_cart(cart.id)

        for line in lines:
            line.status = CartLineStatus.REMOVED
            await self.line_repository.save(line)

        cart.touch()
        await self.cart_repository.save(cart)

        await self.event_bus.publish(
            CartCleared(
                entity_id=cart.id,
                correlation_id=context.correlation_id,
            )
        )

    async def calculate_totals(
        self,
        cart_id: UUID,
    ) -> CartTotals:
        cart = await self.get_cart(cart_id)

        lines = await self.line_repository.list_by_cart(cart.id)

        subtotal = sum(
            (line.subtotal for line in lines),
            Decimal("0"),
        )

        item_count = sum(line.quantity for line in lines)

        return CartTotals(
            subtotal=subtotal,
            item_count=item_count,
            currency=cart.currency,
        )

    async def change_status(
        self,
        *,
        context: CoreContext,
        cart_id: UUID,
        target: CartStatus,
    ) -> Cart:
        cart = await self.get_cart(cart_id)

        validate_cart_transition(
            cart.status,
            target,
        )

        cart.status = target
        cart.touch()

        await self.cart_repository.save(cart)

        await self.event_bus.publish(
            CartStatusChanged(
                entity_id=cart.id,
                correlation_id=context.correlation_id,
            )
        )

        return cart
