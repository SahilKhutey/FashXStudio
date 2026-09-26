from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from .entities import (
    Fulfillment,
    FulfillmentLine,
    Shipment,
    ShipmentPackage,
)


class FulfillmentRepository(ABC):
    @abstractmethod
    async def get(
        self,
        fulfillment_id: UUID,
    ) -> Fulfillment | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_order(
        self,
        order_id: UUID,
    ) -> list[Fulfillment]:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        fulfillment: Fulfillment,
    ) -> Fulfillment:
        raise NotImplementedError


class FulfillmentLineRepository(ABC):
    @abstractmethod
    async def save(
        self,
        line: FulfillmentLine,
    ) -> FulfillmentLine:
        raise NotImplementedError

    @abstractmethod
    async def list_by_fulfillment(
        self,
        fulfillment_id: UUID,
    ) -> list[FulfillmentLine]:
        raise NotImplementedError


class ShipmentRepository(ABC):
    @abstractmethod
    async def get(
        self,
        shipment_id: UUID,
    ) -> Shipment | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_fulfillment(
        self,
        fulfillment_id: UUID,
    ) -> list[Shipment]:
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        shipment: Shipment,
    ) -> Shipment:
        raise NotImplementedError


class ShipmentPackageRepository(ABC):
    @abstractmethod
    async def save(
        self,
        package: ShipmentPackage,
    ) -> ShipmentPackage:
        raise NotImplementedError

    @abstractmethod
    async def list_by_shipment(
        self,
        shipment_id: UUID,
    ) -> list[ShipmentPackage]:
        raise NotImplementedError
