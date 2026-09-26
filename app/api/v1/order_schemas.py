from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class OrderResponse(BaseModel):
    id: UUID
    order_number: str
    customer_id: UUID | None = None
    status: str
    currency: str
    subtotal: Decimal
    discount_total: Decimal
    shipping_total: Decimal
    tax_total: Decimal
    grand_total: Decimal
