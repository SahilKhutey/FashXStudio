import pytest

from api.app.features.product.availability import product_availability
from api.app.features.product.contracts import ProductRequest, VariantSelection
from api.app.features.product.enums import AvailabilityStatus
from api.app.features.product.errors import VariantUnavailableError
from api.app.features.product.models import Product, ProductVariant
from api.app.features.product.repository import ProductRepository
from api.app.features.product.service import ProductService


def product() -> Product:
    return Product(
        "p1",
        "sku",
        "Black Shirt",
        "Everyday",
        "shirts",
        regions=("IN",),
        variants=(
            ProductVariant("v1", "sku-m", "black", "M"),
            ProductVariant(
                "v2", "sku-xl", "black", "XL", availability=AvailabilityStatus.OUT_OF_STOCK
            ),
        ),
        related_product_ids=("p2",),
    )


def test_product_detail_variant_and_related_contracts() -> None:
    related = Product("p2", "sku2", "Jeans", "", "jeans")
    service = ProductService(ProductRepository((product(), related)))
    detail = service.get_product(ProductRequest("user", "p1", "IN"))
    assert detail.product.name == "Black Shirt" and detail.related_products == (related,)
    assert service.select_variant(VariantSelection("p1", "v1")).size == "M"
    with pytest.raises(VariantUnavailableError):
        service.select_variant(VariantSelection("p1", "v2"))


def test_product_availability_and_regional_hook() -> None:
    assert product_availability(product()) == AvailabilityStatus.AVAILABLE
    assert (
        ProductService(ProductRepository((product(),)))
        .get_product(ProductRequest("user", "p1", "US"))
        .available_variants
        == ()
    )
