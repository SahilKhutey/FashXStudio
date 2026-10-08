from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from .entities import (
    InventoryItem,
    StockLocation,
    StockMovement,
)


class StockLocationRepository(ABC):

    @abstractmethod
    async def get(
        self,
        location_id: UUID,
    ) -> StockLocation | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_code(
        self,
        code: str,
    ) -> StockLocation | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        location: StockLocation,
    ) -> StockLocation:
        raise NotImplementedError


class InventoryRepository(ABC):

    @abstractmethod
    async def get(
        self,
        inventory_id: UUID,
    ) -> InventoryItem | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_variant_location(
        self,
        variant_id: UUID,
        location_id: UUID,
    ) -> InventoryItem | None:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        inventory: InventoryItem,
    ) -> InventoryItem:
        raise NotImplementedError

    @abstractmethod
    async def list_by_variant(
        self,
        variant_id: UUID,
    ) -> list[InventoryItem]:
        raise NotImplementedError


class StockMovementRepository(ABC):

    @abstractmethod
    async def save(
        self,
        movement: StockMovement,
    ) -> StockMovement:
        raise NotImplementedError

    @abstractmethod
    async def list_by_inventory(
        self,
        inventory_id: UUID,
    ) -> list[StockMovement]:
        raise NotImplementedError
