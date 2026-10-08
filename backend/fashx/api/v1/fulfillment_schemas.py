from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class AddressRequest(BaseModel):
    recipient_name: str
    address_line_1: str
    address_line_2: str = ""
    city: str
    state: str
    postal_code: str
    country: str = "IN"
    phone: str | None = None


class FulfillmentLineRequest(BaseModel):
    order_line_id: UUID
    product_id: UUID
    variant_id: UUID | None = None
    quantity: int = Field(ge=1)


class FulfillmentCreateRequest(BaseModel):
    order_id: UUID
    shipping_method: str = "standard"
    address: AddressRequest
    lines: list[FulfillmentLineRequest]


class FulfillmentResponse(BaseModel):
    id: UUID
    order_id: UUID
    status: str


class ShipmentCreateRequest(BaseModel):
    shipping_method: str = "standard"
    carrier: str


class ShipmentResponse(BaseModel):
    id: UUID
    fulfillment_id: UUID
    carrier: str
    tracking_number: str | None
    status: str
