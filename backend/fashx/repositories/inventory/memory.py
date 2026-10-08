from __future__ import annotations

from uuid import UUID

from fashx.core.errors import ConflictError
from fashx.domain.inventory.entities import (
    InventoryItem,
    StockLocation,
    StockMovement,
)
from fashx.domain.inventory.repository import (
    InventoryRepository,
    StockLocationRepository,
    StockMovementRepository,
)


class InMemoryStockLocationRepository(StockLocationRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, StockLocation] = {}

    async def get(
        self,
        location_id: UUID,
    ) -> StockLocation | None:
        return self._items.get(location_id)

    async def get_by_code(
        self,
        code: str,
    ) -> StockLocation | None:
        normalized = code.strip().lower()

        for item in self._items.values():
            if item.code.lower() == normalized:
                return item

        return None

    async def save(
        self,
        location: StockLocation,
    ) -> StockLocation:
        existing = await self.get_by_code(location.code)

        if existing is not None and existing.id != location.id:
            raise ConflictError(
                "Stock location code already exists.",
                {"code": location.code},
            )

        self._items[location.id] = location
        return location


class InMemoryInventoryRepository(InventoryRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, InventoryItem] = {}

    async def get(
        self,
        inventory_id: UUID,
    ) -> InventoryItem | None:
        return self._items.get(inventory_id)

    async def get_by_variant_location(
        self,
        variant_id: UUID,
        location_id: UUID,
    ) -> InventoryItem | None:
        for item in self._items.values():
            if (
                item.variant_id == variant_id
                and item.location_id == location_id
            ):
                return item

        return None

    async def save(
        self,
        inventory: InventoryItem,
    ) -> InventoryItem:
        existing = await self.get_by_variant_location(
            inventory.variant_id,
            inventory.location_id,
        )

        if existing is not None and existing.id != inventory.id:
            raise ConflictError(
                "Inventory already exists for this variant and location."
            )

        self._items[inventory.id] = inventory
        return inventory

    async def list_by_variant(
        self,
        variant_id: UUID,
    ) -> list[InventoryItem]:
        return [
            item
            for item in self._items.values()
            if item.variant_id == variant_id
        ]


class InMemoryStockMovementRepository(StockMovementRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, StockMovement] = {}

    async def save(
        self,
        movement: StockMovement,
    ) -> StockMovement:
        self._items[movement.id] = movement
        return movement

    async def list_by_inventory(
        self,
        inventory_id: UUID,
    ) -> list[StockMovement]:
        return [
            movement
            for movement in self._items.values()
            if movement.inventory_id == inventory_id
        ]
