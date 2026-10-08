from collections.abc import Iterable

from .models import Product


class ProductRepository:
    def __init__(self, products: Iterable[Product] = ()) -> None:
        self._products = list(products)

    def all(self) -> tuple[Product, ...]:
        return tuple(self._products)

    def get(self, product_id: str) -> Product | None:
        return next((p for p in self._products if p.product_id == product_id), None)
