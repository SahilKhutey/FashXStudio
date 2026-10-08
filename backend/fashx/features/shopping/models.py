from dataclasses import dataclass, field


@dataclass(frozen=True)
class ComparableProduct:
    product_id: str
    name: str
    price: float
    currency: str = "INR"
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class WishlistItem:
    user_id: str
    product_id: str


@dataclass(frozen=True)
class Comparison:
    user_id: str
    products: tuple[ComparableProduct, ...]
