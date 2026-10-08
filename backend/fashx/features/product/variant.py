from .enums import AvailabilityStatus
from .errors import VariantNotFoundError, VariantUnavailableError
from .models import Product, ProductVariant


def get_variant(product: Product, variant_id: str) -> ProductVariant:
    variant = next((item for item in product.variants if item.variant_id == variant_id), None)
    if variant is None:
        raise VariantNotFoundError(f"Variant not found: {variant_id}")
    return variant


def ensure_variant_available(variant: ProductVariant) -> None:
    if variant.availability in {AvailabilityStatus.OUT_OF_STOCK, AvailabilityStatus.UNAVAILABLE}:
        raise VariantUnavailableError(f"Variant unavailable: {variant.variant_id}")
