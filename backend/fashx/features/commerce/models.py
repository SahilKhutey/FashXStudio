from dataclasses import dataclass, field
from enum import StrEnum


class OrderStatus(StrEnum):
    DRAFT = "draft"
    PLACED = "placed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class CartLine:
    product_id: str
    variant_id: str | None
    quantity: int
    unit_price: float


@dataclass(frozen=True)
class Cart:
    user_id: str
    lines: tuple[CartLine, ...] = ()

    @property
    def total(self) -> float:
        return sum(line.quantity * line.unit_price for line in self.lines)


@dataclass(frozen=True)
class Order:
    order_id: str
    user_id: str
    lines: tuple[CartLine, ...]
    total: float
    status: OrderStatus = OrderStatus.DRAFT
    metadata: dict[str, str] = field(default_factory=dict)
