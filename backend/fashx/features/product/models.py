from collections.abc import Mapping
from dataclasses import dataclass, field

from .enums import AvailabilityStatus, ProductStatus


@dataclass(frozen=True)
class ProductImage:
    image_id: str
    url: str
    alt_text: str = ""
    position: int = 0


@dataclass(frozen=True)
class ProductVariant:
    variant_id: str
    sku: str
    color: str
    size: str | None = None
    price: float = 0.0
    availability: AvailabilityStatus = AvailabilityStatus.AVAILABLE
    stock_quantity: int | None = None


@dataclass(frozen=True)
class Product:
    product_id: str
    sku: str
    name: str
    description: str
    category: str
    brand: str | None = None
    images: tuple[ProductImage, ...] = ()
    variants: tuple[ProductVariant, ...] = ()
    styles: tuple[str, ...] = ()
    colors: tuple[str, ...] = ()
    occasions: tuple[str, ...] = ()
    fits: tuple[str, ...] = ()
    seasons: tuple[str, ...] = ()
    price: float = 0.0
    currency: str = "INR"
    regions: tuple[str, ...] = ()
    status: ProductStatus = ProductStatus.ACTIVE
    related_product_ids: tuple[str, ...] = ()
    related_outfit_ids: tuple[str, ...] = ()
    related_content_ids: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ProductDetail:
    product: Product
    selected_variant: ProductVariant | None
    available_variants: tuple[ProductVariant, ...]
    related_products: tuple[Product, ...]
