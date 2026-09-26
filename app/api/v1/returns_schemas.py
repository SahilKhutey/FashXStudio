from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ReturnLineRequest(BaseModel):
    order_line_id: UUID
    product_id: UUID
    variant_id: UUID | None = None
    quantity: int = Field(ge=1)
    refund_amount: Decimal = Field(ge=0)


class ReturnCreateRequest(BaseModel):
    order_id: UUID
    customer_id: UUID
    reason: str
    notes: str = ""
    lines: list[ReturnLineRequest]


class ReturnResponse(BaseModel):
    id: UUID
    order_id: UUID
    status: str


class CancellationCreateRequest(BaseModel):
    order_id: UUID
    customer_id: UUID
    reason: str


class CancellationResponse(BaseModel):
    id: UUID
    order_id: UUID
    status: str


class RefundCreateRequest(BaseModel):
    order_id: UUID
    return_id: UUID | None = None
    payment_id: UUID | None = None
    amount: Decimal = Field(gt=0)
    currency: str = "INR"
    reason: str


class RefundResponse(BaseModel):
    id: UUID
    order_id: UUID
    amount: Decimal
    currency: str
    status: str
