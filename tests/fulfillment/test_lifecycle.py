from __future__ import annotations

import pytest

from fashx.core.errors import ValidationError
from fashx.domain.fulfillment.enums import (
    FulfillmentStatus,
    ShipmentStatus,
)
from fashx.domain.fulfillment.lifecycle import (
    validate_fulfillment_transition,
    validate_shipment_transition,
)


def test_fulfillment_created_to_processing() -> None:
    validate_fulfillment_transition(
        FulfillmentStatus.CREATED,
        FulfillmentStatus.PROCESSING,
    )


def test_fulfillment_processing_to_ready() -> None:
    validate_fulfillment_transition(
        FulfillmentStatus.PROCESSING,
        FulfillmentStatus.READY,
    )


def test_fulfillment_ready_to_completed() -> None:
    validate_fulfillment_transition(
        FulfillmentStatus.READY,
        FulfillmentStatus.COMPLETED,
    )


def test_fulfillment_cancellations() -> None:
    validate_fulfillment_transition(
        FulfillmentStatus.CREATED,
        FulfillmentStatus.CANCELLED,
    )
    validate_fulfillment_transition(
        FulfillmentStatus.PROCESSING,
        FulfillmentStatus.CANCELLED,
    )


def test_completed_fulfillment_terminal() -> None:
    with pytest.raises(
        ValidationError, match="Invalid fulfillment status transition"
    ):
        validate_fulfillment_transition(
            FulfillmentStatus.COMPLETED,
            FulfillmentStatus.CANCELLED,
        )


def test_cancelled_fulfillment_terminal() -> None:
    with pytest.raises(
        ValidationError, match="Invalid fulfillment status transition"
    ):
        validate_fulfillment_transition(
            FulfillmentStatus.CANCELLED,
            FulfillmentStatus.CREATED,
        )


def test_shipment_normal_flow() -> None:
    validate_shipment_transition(
        ShipmentStatus.CREATED,
        ShipmentStatus.LABEL_CREATED,
    )
    validate_shipment_transition(
        ShipmentStatus.LABEL_CREATED,
        ShipmentStatus.PICKED_UP,
    )
    validate_shipment_transition(
        ShipmentStatus.PICKED_UP,
        ShipmentStatus.IN_TRANSIT,
    )
    validate_shipment_transition(
        ShipmentStatus.IN_TRANSIT,
        ShipmentStatus.OUT_FOR_DELIVERY,
    )
    validate_shipment_transition(
        ShipmentStatus.OUT_FOR_DELIVERY,
        ShipmentStatus.DELIVERED,
    )


def test_shipment_failure_and_retry() -> None:
    validate_shipment_transition(
        ShipmentStatus.IN_TRANSIT,
        ShipmentStatus.DELIVERY_FAILED,
    )
    validate_shipment_transition(
        ShipmentStatus.OUT_FOR_DELIVERY,
        ShipmentStatus.DELIVERY_FAILED,
    )
    validate_shipment_transition(
        ShipmentStatus.DELIVERY_FAILED,
        ShipmentStatus.OUT_FOR_DELIVERY,
    )
    validate_shipment_transition(
        ShipmentStatus.DELIVERY_FAILED,
        ShipmentStatus.CANCELLED,
    )


def test_delivered_terminal() -> None:
    with pytest.raises(
        ValidationError, match="Invalid shipment status transition"
    ):
        validate_shipment_transition(
            ShipmentStatus.DELIVERED,
            ShipmentStatus.IN_TRANSIT,
        )


def test_cancelled_shipment_terminal() -> None:
    with pytest.raises(
        ValidationError, match="Invalid shipment status transition"
    ):
        validate_shipment_transition(
            ShipmentStatus.CANCELLED,
            ShipmentStatus.CREATED,
        )
