from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from fashx.core.errors import ValidationError
from fashx.core.ids import new_id

from .enums import (
    DeliveryStatus,
    FulfillmentLineStatus,
    FulfillmentStatus,
    ShipmentStatus,
    ShippingMethod,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class AddressSnapshot:
    recipient_name: str
    address_line_1: str
    address_line_2: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = "IN"
    phone: str | None = None

    def validate(self) -> None:
        required = {
            "recipient_name": self.recipient_name,
            "address_line_1": self.address_line_1,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
        }

        for field_name, value in required.items():
            if not value.strip():
                raise ValidationError(
                    f"{field_name} is required."
                )


@dataclass(slots=True)
class FulfillmentLine:
    id: UUID = field(default_factory=new_id)
    fulfillment_id: UUID | None = None
    order_line_id: UUID | None = None
    product_id: UUID | None = None
    variant_id: UUID | None = None
    quantity: int = 1
    status: FulfillmentLineStatus = (
        FulfillmentLineStatus.PENDING
    )
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def validate(self) -> None:
        if self.fulfillment_id is None:
            raise ValidationError(
                "Fulfillment line requires fulfillment ID."
            )

        if self.order_line_id is None:
            raise ValidationError(
                "Fulfillment line requires order line ID."
            )

        if self.product_id is None:
            raise ValidationError(
                "Fulfillment line requires product ID."
            )

        if self.quantity < 1:
            raise ValidationError(
                "Fulfillment quantity must be at least 1."
            )


@dataclass(slots=True)
class Fulfillment:
    id: UUID = field(default_factory=new_id)
    order_id: UUID | None = None
    status: FulfillmentStatus = FulfillmentStatus.CREATED
    shipping_method: ShippingMethod = (
        ShippingMethod.STANDARD
    )
    address: AddressSnapshot | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1

    def validate(self) -> None:
        if self.order_id is None:
            raise ValidationError(
                "Fulfillment requires order ID."
            )

        if self.address is None:
            raise ValidationError(
                "Fulfillment requires delivery address."
            )

        self.address.validate()

        if self.version < 1:
            raise ValidationError(
                "Fulfillment version must be positive."
            )

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1


@dataclass(slots=True)
class ShipmentPackage:
    id: UUID = field(default_factory=new_id)
    shipment_id: UUID | None = None
    weight_grams: int = 0
    length_cm: float = 0.0
    width_cm: float = 0.0
    height_cm: float = 0.0
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if self.shipment_id is None:
            raise ValidationError(
                "Package requires shipment ID."
            )

        if self.weight_grams < 0:
            raise ValidationError(
                "Package weight cannot be negative."
            )


@dataclass(slots=True)
class Shipment:
    id: UUID = field(default_factory=new_id)
    fulfillment_id: UUID | None = None
    carrier: str = ""
    service_code: str = ""
    tracking_number: str | None = None
    status: ShipmentStatus = ShipmentStatus.CREATED
    shipping_method: ShippingMethod = (
        ShippingMethod.STANDARD
    )
    delivery_status: DeliveryStatus = (
        DeliveryStatus.PENDING
    )
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if self.fulfillment_id is None:
            raise ValidationError(
                "Shipment requires fulfillment ID."
            )

        if not self.carrier.strip():
            raise ValidationError(
                "Shipment carrier is required."
            )

        if self.version < 1:
            raise ValidationError(
                "Shipment version must be positive."
            )

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1
