from uuid import uuid4

from .models import Cart, CartLine, Order, OrderStatus


class CommerceService:
    """F11 local order lifecycle; payment and fulfillment are adapter boundaries."""

    def __init__(self) -> None:
        self._carts: dict[str, Cart] = {}
        self._orders: dict[str, Order] = {}

    def cart(self, user_id: str) -> Cart:
        return self._carts.get(user_id, Cart(user_id))

    def add_line(self, user_id: str, line: CartLine) -> Cart:
        if not user_id.strip() or line.quantity < 1 or line.unit_price < 0:
            raise ValueError("Invalid cart line")
        cart = self.cart(user_id)
        cart = Cart(user_id, (*cart.lines, line))
        self._carts[user_id] = cart
        return cart

    def place_order(self, user_id: str, idempotency_key: str) -> Order:
        if not idempotency_key.strip():
            raise ValueError("idempotency_key is required")
        for order in self._orders.values():
            if order.user_id == user_id and order.metadata.get("idempotency_key") == idempotency_key:
                return order
        cart = self.cart(user_id)
        if not cart.lines:
            raise ValueError("Cannot place an empty order")
        order = Order(str(uuid4()), user_id, cart.lines, cart.total, OrderStatus.PLACED, {"idempotency_key": idempotency_key})
        self._orders[order.order_id] = order
        self._carts[user_id] = Cart(user_id)
        return order
