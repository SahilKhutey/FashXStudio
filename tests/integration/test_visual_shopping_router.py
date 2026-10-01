"""Integration tests for Shopping UI System REST API endpoints — Phase 07.

Tests Shopping Flows A, B, C, D (Section 7.76) and REST endpoints:
- Shopping Flow A: Search -> Product Detail -> Add to Cart -> Cart -> Checkout
- Shopping Flow B: Product -> Wishlist Toggle -> Check Wishlist
- Shopping Flow C: Product -> Complete the Look -> Add constituent to Cart
- Shopping Flow D: Cart -> Validate Pre-checkout
- Template Endpoints (SH01 - SH12)
"""

from fastapi.testclient import TestClient
from api.app.main import app

client = TestClient(app)


def test_shopping_flow_a_search_to_cart_to_checkout() -> None:
    """Shopping Flow A (Section 7.76): Search -> Product Detail -> Add to Cart -> Cart -> Checkout."""
    # 1. Search for 'denim'
    res_search = client.get("/api/v1/visual/shopping/search?q=denim")
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert search_data["total_results"] >= 1
    assert "prod-denim-01" in search_data["product_ids"]

    # 2. Get Product Detail
    res_prod = client.get("/api/v1/visual/shopping/product/prod-denim-01")
    assert res_prod.status_code == 200
    prod_data = res_prod.json()
    assert prod_data["title"] == "Selvedge Oversized Denim Jacket"
    assert prod_data["availability"] == "in_stock"

    # 3. Add to Cart with selected variant
    add_req = {
        "product_id": "prod-denim-01",
        "quantity": 1,
        "selected_variants": {"color": "raw_indigo", "size": "M"},
    }
    res_add = client.post("/api/v1/visual/shopping/cart/add?cart_id=flow-a-cart", json=add_req)
    assert res_add.status_code == 200
    cart_data = res_add.json()
    assert len(cart_data["items"]) >= 1
    assert cart_data["summary"]["total"] >= 4999.0

    # 4. Retrieve Cart
    res_cart = client.get("/api/v1/visual/shopping/cart?cart_id=flow-a-cart")
    assert res_cart.status_code == 200
    assert res_cart.json()["cart_id"] == "flow-a-cart"

    # 5. Access Checkout Template
    res_chk = client.get("/api/v1/visual/shopping/templates/checkout?checkout_id=flow-a-chk")
    assert res_chk.status_code == 200
    chk_data = res_chk.json()
    assert chk_data["screen_id"] == "SH08"
    assert len(chk_data["available_addresses"]) >= 1


def test_shopping_flow_b_wishlist_toggle_and_retrieval() -> None:
    """Shopping Flow B (Section 7.76): Product -> Wishlist Save -> View Wishlist."""
    # 1. Save product to wishlist
    toggle_req = {
        "product_id": "prod-denim-01",
        "currently_wishlisted": False,
    }
    res_toggle = client.post("/api/v1/visual/shopping/wishlist/toggle?user_id=flow-b-user", json=toggle_req)
    assert res_toggle.status_code == 200
    toggle_data = res_toggle.json()
    assert toggle_data["is_in_wishlist"] is True
    assert toggle_data["total_wishlist_count"] >= 1

    # 2. Get Wishlist Template
    res_wl = client.get("/api/v1/visual/shopping/templates/wishlist?user_id=flow-b-user")
    assert res_wl.status_code == 200
    wl_data = res_wl.json()
    assert wl_data["screen_id"] == "SH05"
    assert any(item["product_id"] == "prod-denim-01" for item in wl_data["wishlist"]["items"])


def test_shopping_flow_c_complete_the_look_cross_sell() -> None:
    """Shopping Flow C (Section 7.76): Product -> Complete the Look -> Add related item to Cart."""
    # 1. Fetch denim jacket product detail
    res_prod = client.get("/api/v1/visual/shopping/product/prod-denim-01")
    assert res_prod.status_code == 200
    prod_data = res_prod.json()
    look_slots = prod_data["complete_the_look"]
    assert len(look_slots) >= 1

    # 2. Get cross-sell item ID (linen shirt)
    cross_sell_id = look_slots[0]["product_id"]
    assert cross_sell_id == "prod-linen-02"

    # 3. Add cross-sell item to cart
    add_req = {
        "product_id": cross_sell_id,
        "quantity": 1,
        "selected_variants": {"size": "L"},
    }
    res_add = client.post("/api/v1/visual/shopping/cart/add?cart_id=flow-c-cart", json=add_req)
    assert res_add.status_code == 200
    assert any(i["product_id"] == "prod-linen-02" for i in res_add.json()["items"])


def test_shopping_flow_d_cart_validation() -> None:
    """Shopping Flow D (Section 7.76): Cart -> Pre-checkout availability and price validation."""
    res_val = client.get("/api/v1/visual/shopping/cart/validate?cart_id=cart-user-1")
    assert res_val.status_code == 200
    data = res_val.json()
    assert data["is_valid"] is True
    assert data["has_out_of_stock"] is False


def test_shopping_product_not_found() -> None:
    """GET /api/v1/visual/shopping/product/unknown returns 404."""
    res = client.get("/api/v1/visual/shopping/product/unknown-prod-xyz")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_product_comparison_endpoint() -> None:
    """POST /api/v1/visual/shopping/compare returns side-by-side attribute matrix."""
    res = client.post(
        "/api/v1/visual/shopping/compare",
        json=["prod-denim-01", "prod-linen-02"],
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["product_ids"]) == 2
    assert len(data["attributes"]) >= 3


def test_cart_quantity_update_endpoint() -> None:
    """POST /api/v1/visual/shopping/cart/update modifies quantity and totals."""
    # First ensure item is in cart
    client.post(
        "/api/v1/visual/shopping/cart/add?cart_id=cart-qty-test",
        json={"product_id": "prod-denim-01", "quantity": 1, "selected_variants": {}},
    )
    # Fetch cart to get item_id
    cart = client.get("/api/v1/visual/shopping/cart?cart_id=cart-qty-test").json()
    item_id = cart["items"][0]["item_id"]

    # Update to 2
    update_res = client.post(
        "/api/v1/visual/shopping/cart/update?cart_id=cart-qty-test",
        json={"item_id": item_id, "quantity": 2},
    )
    assert update_res.status_code == 200
    assert update_res.json()["items"][0]["quantity"] == 2


def test_shopping_templates_endpoints() -> None:
    """GET /api/v1/visual/shopping/templates/* returns valid template specs."""
    # SH01: Home
    res_home = client.get("/api/v1/visual/shopping/templates/home")
    assert res_home.status_code == 200
    assert res_home.json()["screen_id"] == "SH01"

    # SH02: Category
    res_cat = client.get("/api/v1/visual/shopping/templates/category/outerwear")
    assert res_cat.status_code == 200
    assert res_cat.json()["screen_id"] == "SH02"

    # SH07: Product Detail
    res_detail = client.get("/api/v1/visual/shopping/templates/product-detail/prod-denim-01")
    assert res_detail.status_code == 200
    assert res_detail.json()["product"]["id"] == "prod-denim-01"

    # SH06: Cart
    res_cart = client.get("/api/v1/visual/shopping/templates/cart")
    assert res_cart.status_code == 200
    assert res_cart.json()["screen_id"] == "SH06"

    # SH09: Order Review
    res_rev = client.get("/api/v1/visual/shopping/templates/order-review")
    assert res_rev.status_code == 200
    assert res_rev.json()["screen_id"] == "SH09"

    # SH10: Confirmation
    res_conf = client.get("/api/v1/visual/shopping/templates/confirmation")
    assert res_conf.status_code == 200
    assert res_conf.json()["screen_id"] == "SH10"

    # SH11: Orders
    res_orders = client.get("/api/v1/visual/shopping/templates/orders")
    assert res_orders.status_code == 200
    assert res_orders.json()["screen_id"] == "SH11"

    # SH12: Order Detail
    res_ord_det = client.get("/api/v1/visual/shopping/templates/order-detail/ord-98210")
    assert res_ord_det.status_code == 200
    assert res_ord_det.json()["screen_id"] == "SH12"
