from .contracts import ProductInteraction, ProductRequest, VariantSelection
from .errors import ProductNotFoundError, ProductUnavailableError
from .models import ProductDetail, ProductVariant
from .repository import ProductRepository
from .variant import ensure_variant_available, get_variant


class ProductService:
    def __init__(self, repository: ProductRepository) -> None:
        self.repository = repository

    def get_product(self, request: ProductRequest) -> ProductDetail:
        product = self.repository.get(request.product_id)
        if product is None:
            raise ProductNotFoundError(request.product_id)
        if product.status.value in {"draft", "discontinued"}:
            raise ProductUnavailableError(request.product_id)
        variants = (
            product.variants
            if not request.region or not product.regions or request.region in product.regions
            else ()
        )
        related = tuple(
            item for item in self.repository.all() if item.product_id in product.related_product_ids
        )
        return ProductDetail(product, None, variants, related)

    def select_variant(self, selection: VariantSelection) -> ProductVariant:
        product = self.repository.get(selection.product_id)
        if product is None:
            raise ProductNotFoundError(selection.product_id)
        variant = get_variant(product, selection.variant_id)
        ensure_variant_available(variant)
        return variant

    def record_interaction(self, interaction: ProductInteraction) -> None:
        del interaction
