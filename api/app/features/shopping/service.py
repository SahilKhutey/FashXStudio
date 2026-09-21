from .models import ComparableProduct, Comparison, WishlistItem


class ShoppingService:
    """F10 decision support; product ownership remains with F05."""

    def __init__(self) -> None:
        self._wishlists: dict[str, set[str]] = {}

    def save(self, user_id: str, product_id: str) -> WishlistItem:
        if not user_id.strip() or not product_id.strip():
            raise ValueError("user_id and product_id are required")
        self._wishlists.setdefault(user_id, set()).add(product_id)
        return WishlistItem(user_id, product_id)

    def wishlist(self, user_id: str) -> tuple[str, ...]:
        return tuple(sorted(self._wishlists.get(user_id, set())))

    def compare(self, user_id: str, products: tuple[ComparableProduct, ...]) -> Comparison:
        if not user_id.strip() or len(products) < 2:
            raise ValueError("Comparison requires a user and at least two products")
        if len({item.product_id for item in products}) != len(products):
            raise ValueError("Comparison products must be unique")
        return Comparison(user_id, products)
