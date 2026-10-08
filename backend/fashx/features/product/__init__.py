"""F05 Product Experience feature module."""

from .availability import product_availability
from .contracts import ProductInteraction, ProductRequest, VariantSelection
from .models import Product, ProductDetail, ProductImage, ProductVariant
from .service import ProductService

__all__ = [
    "Product",
    "ProductDetail",
    "ProductImage",
    "ProductInteraction",
    "ProductRequest",
    "ProductService",
    "ProductVariant",
    "VariantSelection",
    "product_availability",
]
