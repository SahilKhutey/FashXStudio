from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.core.context import CoreContext
from app.core.errors import (
    ConflictError,
    NotFoundError,
)
from app.core.event_bus import EventBus

from .carrier import CarrierProvider
from .entities import (
    Fulfillment,
    FulfillmentLine,
    Shipment,
)
from .enums import (
    DeliveryStatus,
    FulfillmentStatus,
    ShipmentStatus,
)
from .events import (
    FulfillmentCreated,
    FulfillmentStatusChanged,
    ShipmentCreated,
    ShipmentDelivered,
    ShipmentStatusChanged,
)
from .lifecycle import (
    validate_fulfillment_transition,
    validate_shipment_transition,
)
from .repository import (
    FulfillmentLineRepository,
    FulfillmentRepository,
    ShipmentRepository,
)


@dataclass(slots=True)
class FulfillmentService:
    fulfillment_repository: FulfillmentRepository
    line_repository: FulfillmentLineRepository
    shipment_repository: ShipmentRepository
    event_bus: EventBus
    carrier: CarrierProvider

    async def create_fulfillment(
        self,
        *,
        context: CoreContext,
        fulfillment: Fulfillment,
        lines: list[FulfillmentLine],
    ) -> Fulfillment:
        fulfillment.validate()

        if not lines:
            raise ConflictError(
                "Fulfillment requires at least one line."
            )

        for line in lines:
            line.fulfillment_id = fulfillment.id
            line.validate()
            await self.line_repository.save(line)

        await self.fulfillment_repository.save(fulfillment)

        await self.event_bus.publish(
            FulfillmentCreated(
                entity_id=fulfillment.id,
                correlation_id=context.correlation_id,
            )
        )

        return fulfillment

    async def get_fulfillment(
        self,
        fulfillment_id: UUID,
    ) -> Fulfillment:
        result = await self.fulfillment_repository.get(
            fulfillment_id
        )

        if result is None:
            raise NotFoundError(
                "Fulfillment was not found.",
                {"fulfillment_id": str(fulfillment_id)},
            )

        return result

    async def change_fulfillment_status(
        self,
        *,
        context: CoreContext,
        fulfillment_id: UUID,
        target: FulfillmentStatus,
    ) -> Fulfillment:
        fulfillment = await self.get_fulfillment(fulfillment_id)

        validate_fulfillment_transition(
            fulfillment.status,
            target,
        )

        fulfillment.status = target
        fulfillment.touch()

        await self.fulfillment_repository.save(fulfillment)

        await self.event_bus.publish(
            FulfillmentStatusChanged(
                entity_id=fulfillment.id,
                correlation_id=context.correlation_id,
            )
        )

        return fulfillment

    async def create_shipment(
        self,
        *,
        context: CoreContext,
        fulfillment_id: UUID,
        shipment: Shipment,
    ) -> Shipment:
        fulfillment = await self.get_fulfillment(fulfillment_id)

        if fulfillment.status not in {
            FulfillmentStatus.PROCESSING,
            FulfillmentStatus.READY,
        }:
            raise ConflictError(
                "Shipment cannot be created from the current fulfillment state."
            )

        shipment.fulfillment_id = fulfillment.id
        shipment.validate()

        address_dict = {}
        if fulfillment.address:
            address_dict = {
                "recipient_name": fulfillment.address.recipient_name,
                "address_line_1": fulfillment.address.address_line_1,
                "address_line_2": fulfillment.address.address_line_2,
                "city": fulfillment.address.city,
                "state": fulfillment.address.state,
                "postal_code": fulfillment.address.postal_code,
                "country": fulfillment.address.country,
            }

        result = await self.carrier.create_shipment(
            shipment_id=str(shipment.id),
            shipping_method=shipment.shipping_method.value,
            address=address_dict,
        )

        if not result.success:
            raise ConflictError(
                "Carrier failed to create shipment.",
                {
                    "error_code": result.error_code,
                    "error_message": result.error_message,
                },
            )

        shipment.tracking_number = result.tracking_number
        shipment.metadata["provider_shipment_id"] = (
            result.provider_shipment_id or ""
        )
        shipment.status = ShipmentStatus.LABEL_CREATED
        shipment.touch()

        await self.shipment_repository.save(shipment)

        await self.event_bus.publish(
            ShipmentCreated(
                entity_id=shipment.id,
                correlation_id=context.correlation_id,
            )
        )

        return shipment

    async def change_shipment_status(
        self,
        *,
        context: CoreContext,
        shipment_id: UUID,
        target: ShipmentStatus,
    ) -> Shipment:
        shipment = await self.shipment_repository.get(shipment_id)

        if shipment is None:
            raise NotFoundError(
                "Shipment was not found.",
                {"shipment_id": str(shipment_id)},
            )

        validate_shipment_transition(
            shipment.status,
            target,
        )

        shipment.status = target

        if target == ShipmentStatus.DELIVERED:
            shipment.delivery_status = DeliveryStatus.DELIVERED

        shipment.touch()

        await self.shipment_repository.save(shipment)

        await self.event_bus.publish(
            ShipmentStatusChanged(
                entity_id=shipment.id,
                correlation_id=context.correlation_id,
            )
        )

        if target == ShipmentStatus.DELIVERED:
            await self.event_bus.publish(
                ShipmentDelivered(
                    entity_id=shipment.id,
                    correlation_id=context.correlation_id,
                )
            )

        return shipment
