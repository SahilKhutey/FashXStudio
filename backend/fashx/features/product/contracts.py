from dataclasses import dataclass


@dataclass(frozen=True)
class ProductRequest:
    user_id: str
    product_id: str
    region: str | None = None


@dataclass(frozen=True)
class VariantSelection:
    product_id: str
    variant_id: str


@dataclass(frozen=True)
class ProductInteraction:
    user_id: str
    product_id: str
    action: str
    variant_id: str | None = None
