from __future__ import annotations

from uuid import UUID

from app.core.context import CoreContext
from app.core.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.event_bus import EventBus

from .entities import (
    InventoryItem,
    StockLocation,
    StockMovement,
)
from .enums import (
    InventoryStatus,
    StockAdjustmentType,
)
from .events import (
    InventoryAdjusted,
    InventoryCreated,
    InventoryStatusChanged,
    StockLocationCreated,
)
from .lifecycle import (
    validate_inventory_transition,
)
from .repository import (
    InventoryRepository,
    StockLocationRepository,
    StockMovementRepository,
)


class InventoryService:
    def __init__(
        self,
        inventory_repository: InventoryRepository,
        location_repository: StockLocationRepository,
        movement_repository: StockMovementRepository,
        event_bus: EventBus,
    ) -> None:
        self.inventory_repository = inventory_repository
        self.location_repository = location_repository
        self.movement_repository = movement_repository
        self.event_bus = event_bus

    async def create_location(
        self,
        *,
        context: CoreContext,
        location: StockLocation,
    ) -> StockLocation:
        location.validate()

        await self.location_repository.save(location)

        await self.event_bus.publish(
            StockLocationCreated(
                entity_id=location.id,
                correlation_id=context.correlation_id,
            )
        )

        return location

    async def create_inventory(
        self,
        *,
        context: CoreContext,
        inventory: InventoryItem,
    ) -> InventoryItem:
        inventory.validate()

        location = await self.location_repository.get(inventory.location_id)
        if location is None:
            raise NotFoundError(
                "Stock location was not found.",
                {"location_id": str(inventory.location_id)},
            )

        existing = await self.inventory_repository.get_by_variant_location(
            inventory.variant_id,
            inventory.location_id,
        )
        if existing is not None:
            raise ConflictError(
                "Inventory already exists for this variant and location."
            )

        await self.inventory_repository.save(inventory)

        await self.event_bus.publish(
            InventoryCreated(
                entity_id=inventory.id,
                correlation_id=context.correlation_id,
            )
        )

        return inventory

    async def get_inventory(
        self,
        inventory_id: UUID,
    ) -> InventoryItem:
        inventory = await self.inventory_repository.get(inventory_id)
        if inventory is None:
            raise NotFoundError(
                "Inventory was not found.",
                {"inventory_id": str(inventory_id)},
            )
        return inventory

    async def list_variant_inventory(
        self,
        variant_id: UUID,
    ) -> list[InventoryItem]:
        return await self.inventory_repository.list_by_variant(variant_id)

    async def adjust_stock(
        self,
        *,
        context: CoreContext,
        inventory_id: UUID,
        adjustment_type: StockAdjustmentType,
        quantity: int,
        reason: str = "",
    ) -> InventoryItem:
        if quantity <= 0:
            raise ValidationError("Stock adjustment quantity must be positive.")

        inventory = await self.get_inventory(inventory_id)

        if inventory.status != InventoryStatus.ACTIVE:
            raise ValidationError("Stock can only be adjusted for active inventory.")

        if adjustment_type in {
            StockAdjustmentType.RECEIVE,
            StockAdjustmentType.ADD,
        }:
            inventory.on_hand += quantity

        elif adjustment_type in {
            StockAdjustmentType.REMOVE,
            StockAdjustmentType.DAMAGE,
            StockAdjustmentType.LOSS,
        }:
            if quantity > inventory.available:
                raise ValidationError("Stock removal exceeds available inventory.")
            inventory.on_hand -= quantity

        elif adjustment_type == StockAdjustmentType.CORRECTION:
            raise ValidationError(
                "Correction requires a dedicated correction workflow."
            )

        inventory.validate()
        inventory.touch()

        await self.inventory_repository.save(inventory)

        movement = StockMovement(
            inventory_id=inventory.id,
            adjustment_type=adjustment_type,
            quantity=quantity,
            reason=reason,
        )

        await self.movement_repository.save(movement)

        await self.event_bus.publish(
            InventoryAdjusted(
                entity_id=inventory.id,
                correlation_id=context.correlation_id,
            )
        )

        return inventory

    async def change_status(
        self,
        *,
        context: CoreContext,
        inventory_id: UUID,
        target: InventoryStatus,
    ) -> InventoryItem:
        inventory = await self.get_inventory(inventory_id)

        validate_inventory_transition(
            inventory.status,
            target,
        )

        inventory.status = target
        inventory.touch()

        await self.inventory_repository.save(inventory)

        await self.event_bus.publish(
            InventoryStatusChanged(
                entity_id=inventory.id,
                correlation_id=context.correlation_id,
            )
        )

        return inventory
