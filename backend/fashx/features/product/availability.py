from .enums import AvailabilityStatus, ProductStatus
from .models import Product


def product_availability(product: Product) -> AvailabilityStatus:
    if not product.variants:
        return (
            AvailabilityStatus.OUT_OF_STOCK
            if product.status == ProductStatus.OUT_OF_STOCK
            else AvailabilityStatus.AVAILABLE
        )
    states = {variant.availability for variant in product.variants}
    if not states & {AvailabilityStatus.AVAILABLE, AvailabilityStatus.LOW_STOCK}:
        return AvailabilityStatus.OUT_OF_STOCK
    return (
        AvailabilityStatus.LOW_STOCK
        if AvailabilityStatus.LOW_STOCK in states
        else AvailabilityStatus.AVAILABLE
    )
