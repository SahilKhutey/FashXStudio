from __future__ import annotations

from enum import StrEnum


class FulfillmentStatus(StrEnum):
    CREATED = "created"
    PROCESSING = "processing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FulfillmentLineStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class ShipmentStatus(StrEnum):
    CREATED = "created"
    LABEL_CREATED = "label_created"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    DELIVERY_FAILED = "delivery_failed"
    CANCELLED = "cancelled"


class ShippingMethod(StrEnum):
    STANDARD = "standard"
    EXPRESS = "express"
    SAME_DAY = "same_day"
    PICKUP = "pickup"


class DeliveryStatus(StrEnum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"
