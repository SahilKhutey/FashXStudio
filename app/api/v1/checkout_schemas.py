from uuid import UUID

from pydantic import BaseModel


class CheckoutCreateRequest(BaseModel):
    cart_id: UUID
    customer_id: UUID | None = None
    currency: str = "INR"


class CheckoutResponse(BaseModel):
    id: UUID
    cart_id: UUID
    customer_id: UUID | None = None
    status: str
    currency: str
    order_id: UUID | None = None
