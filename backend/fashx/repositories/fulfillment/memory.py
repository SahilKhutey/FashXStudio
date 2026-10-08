from __future__ import annotations

from uuid import UUID

from app.domain.fulfillment.entities import (
    Fulfillment,
    FulfillmentLine,
    Shipment,
    ShipmentPackage,
)
from app.domain.fulfillment.repository import (
    FulfillmentLineRepository,
    FulfillmentRepository,
    ShipmentPackageRepository,
    ShipmentRepository,
)


class InMemoryFulfillmentRepository(FulfillmentRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, Fulfillment] = {}

    async def get(
        self,
        fulfillment_id: UUID,
    ) -> Fulfillment | None:
        return self._items.get(fulfillment_id)

    async def list_by_order(
        self,
        order_id: UUID,
    ) -> list[Fulfillment]:
        return [
            item
            for item in self._items.values()
            if item.order_id == order_id
        ]

    async def save(
        self,
        fulfillment: Fulfillment,
    ) -> Fulfillment:
        self._items[fulfillment.id] = fulfillment
        return fulfillment


class InMemoryFulfillmentLineRepository(
    FulfillmentLineRepository
):
    def __init__(self) -> None:
        self._items: dict[UUID, FulfillmentLine] = {}

    async def save(
        self,
        line: FulfillmentLine,
    ) -> FulfillmentLine:
        self._items[line.id] = line
        return line

    async def list_by_fulfillment(
        self,
        fulfillment_id: UUID,
    ) -> list[FulfillmentLine]:
        return [
            item
            for item in self._items.values()
            if item.fulfillment_id == fulfillment_id
        ]


class InMemoryShipmentRepository(ShipmentRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, Shipment] = {}

    async def get(
        self,
        shipment_id: UUID,
    ) -> Shipment | None:
        return self._items.get(shipment_id)

    async def list_by_fulfillment(
        self,
        fulfillment_id: UUID,
    ) -> list[Shipment]:
        return [
            item
            for item in self._items.values()
            if item.fulfillment_id == fulfillment_id
        ]

    async def save(
        self,
        shipment: Shipment,
    ) -> Shipment:
        self._items[shipment.id] = shipment
        return shipment


class InMemoryShipmentPackageRepository(
    ShipmentPackageRepository
):
    def __init__(self) -> None:
        self._items: dict[UUID, ShipmentPackage] = {}

    async def save(
        self,
        package: ShipmentPackage,
    ) -> ShipmentPackage:
        self._items[package.id] = package
        return package

    async def list_by_shipment(
        self,
        shipment_id: UUID,
    ) -> list[ShipmentPackage]:
        return [
            item
            for item in self._items.values()
            if item.shipment_id == shipment_id
        ]
