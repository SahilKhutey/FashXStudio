from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentCreateRequest(BaseModel):
    order_id: UUID
    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )
    idempotency_key: str | None = Field(
        default=None,
        max_length=200,
    )


class PaymentResponse(BaseModel):
    id: UUID
    order_id: UUID
    amount: Decimal
    currency: str
    status: str
    provider: str


class PaymentAuthorizeRequest(BaseModel):
    payment_method: str = Field(
        min_length=2,
        max_length=100,
    )
