from __future__ import annotations

from fashx.core.errors import ValidationError

from .enums import (
    FulfillmentStatus,
    ShipmentStatus,
)

_FULFILLMENT_TRANSITIONS = {
    FulfillmentStatus.CREATED: {
        FulfillmentStatus.PROCESSING,
        FulfillmentStatus.CANCELLED,
    },
    FulfillmentStatus.PROCESSING: {
        FulfillmentStatus.READY,
        FulfillmentStatus.CANCELLED,
    },
    FulfillmentStatus.READY: {
        FulfillmentStatus.COMPLETED,
    },
    FulfillmentStatus.COMPLETED: set(),
    FulfillmentStatus.CANCELLED: set(),
}

_SHIPMENT_TRANSITIONS = {
    ShipmentStatus.CREATED: {
        ShipmentStatus.LABEL_CREATED,
        ShipmentStatus.CANCELLED,
    },
    ShipmentStatus.LABEL_CREATED: {
        ShipmentStatus.PICKED_UP,
        ShipmentStatus.CANCELLED,
    },
    ShipmentStatus.PICKED_UP: {
        ShipmentStatus.IN_TRANSIT,
    },
    ShipmentStatus.IN_TRANSIT: {
        ShipmentStatus.OUT_FOR_DELIVERY,
        ShipmentStatus.DELIVERY_FAILED,
    },
    ShipmentStatus.OUT_FOR_DELIVERY: {
        ShipmentStatus.DELIVERED,
        ShipmentStatus.DELIVERY_FAILED,
    },
    ShipmentStatus.DELIVERY_FAILED: {
        ShipmentStatus.OUT_FOR_DELIVERY,
        ShipmentStatus.CANCELLED,
    },
    ShipmentStatus.DELIVERED: set(),
    ShipmentStatus.CANCELLED: set(),
}


def validate_fulfillment_transition(
    current: FulfillmentStatus,
    target: FulfillmentStatus,
) -> None:
    if target not in _FULFILLMENT_TRANSITIONS[current]:
        raise ValidationError(
            "Invalid fulfillment status transition.",
            {
                "current": current.value,
                "target": target.value,
            },
        )


def validate_shipment_transition(
    current: ShipmentStatus,
    target: ShipmentStatus,
) -> None:
    if target not in _SHIPMENT_TRANSITIONS[current]:
        raise ValidationError(
            "Invalid shipment status transition.",
            {
                "current": current.value,
                "target": target.value,
            },
        )
