from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DiscountRule:
    discount_type: str
    value: Decimal
    maximum_discount: Decimal | None = None
    minimum_purchase_value: Decimal | None = None
    customer_id: UUID | None = None
    region: str | None = None
