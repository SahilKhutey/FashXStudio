"""Unit tests for Shopping UI System & Commerce Experience — Phase 07.

Covers SHOP-001 through SHOP-053 as defined in Section 7.75:
- Catalog & Product (SHOP-001 - SHOP-005)
- Filters & Sorting (SHOP-010 - SHOP-015)
- Product Detail & Variants (SHOP-020 - SHOP-026)
- Cart & Quantity Control (SHOP-030 - SHOP-035)
- Checkout & Steps (SHOP-040 - SHOP-046)
- Orders & Status (SHOP-050 - SHOP-053)
- Product Comparison & Complete-the-Look
"""

import pytest
from schemas.visual.components import PriceSpecContract, RatingSpecContract
from schemas.visual.shopping import (
    ActiveFilterContract,
    AddToCartRequestContract,
    CartContract,
    CartItemContract,
    CartSummaryContract,
    CategoryTemplateSpecContract,
    CheckoutStateContract,
    CheckoutStep,
    ComparisonAttributeContract,
    CompleteTheLookSlotContract,
    DeliveryAddressContract,
    DeliveryInfoContract,
    DeliveryMethodContract,
    FilterGroupContract,
    FilterOptionContract,
    FilterStateContract,
    FilterType,
    OrderContract,
    OrderItemContract,
    OrderStatus,
    OrdersTemplateSpecContract,
    PaymentMethodContract,
    ProductAvailabilityState,
    ProductComparisonContract,
    ProductDetailTemplateSpecContract,
    ProductVariantGroupContract,
    ProductVariantOptionContract,
    SearchResultsTemplateSpecContract,
    ShoppingHomeTemplateSpecContract,
    ShoppingProductDetailContract,
    ShoppingScreenId,
    ShoppingState,
    SortOption,
    SpecificationAttributeContract,
    UpdateCartQuantityRequestContract,
    VariantState,
    VariantType,
    WishlistContract,
    WishlistItemContract,
    WishlistToggleRequestContract,
)
from api.app.visual.shopping_service import (
    add_item_to_cart,
    compare_products,
    get_cart_template,
    get_category_template,
    get_checkout_template,
    get_confirmation_template,
    get_order_detail_template,
    get_order_review_template,
    get_orders_template,
    get_product_detail,
    get_product_detail_template,
    get_shopping_home_template,
    get_user_cart,
    get_wishlist_template,
    search_catalog_products,
    toggle_user_wishlist,
    update_cart_item_quantity,
    validate_cart_state,
)


# ---------------------------------------------------------------------------
# SHOP-001 - SHOP-005: Catalog & Categories
# ---------------------------------------------------------------------------

def test_shop_001_shopping_home_template() -> None:
    """SHOP-001: ShoppingHomeTemplate combines discovery and commerce."""
    tpl = get_shopping_home_template()
    assert tpl.screen_id == ShoppingScreenId.SH01_SHOPPING_HOME
    assert len(tpl.categories) >= 3
    assert len(tpl.trending_product_ids) >= 1
    assert "selvedge" in tpl.search_placeholder.lower()


def test_shop_002_category_template_hierarchy() -> None:
    """SHOP-002: Category template derives subcategories from catalog taxonomy."""
    cat = get_category_template("outerwear")
    assert cat.screen_id == ShoppingScreenId.SH02_CATEGORY
    assert cat.category_id == "outerwear"
    assert cat.category_name == "Outerwear"
    assert len(cat.subcategories) >= 2


def test_shop_003_catalog_search_with_query() -> None:
    """SHOP-003: Catalog search matches on brand or title query."""
    res = search_catalog_products(query="denim")
    assert res.total_results >= 1
    assert "prod-denim-01" in res.product_ids


def test_shop_004_catalog_search_empty_suggestions() -> None:
    """SHOP-004: Catalog search with zero matches provides helpful keyword suggestions."""
    res = search_catalog_products(query="nonexistent_xyz")
    assert res.total_results == 0
    assert len(res.suggestions) >= 1
    assert any("linen" in s.lower() for s in res.suggestions)


def test_shop_005_extra_fields_forbidden() -> None:
    """SHOP-005: Shopping contracts reject undeclared props via extra='forbid'."""
    with pytest.raises(Exception):
        FilterOptionContract(
            id="opt-1",
            label="Cotton",
            value="cotton",
            unauthorized_field="malicious",  # type: ignore
        )


# ---------------------------------------------------------------------------
# SHOP-010 - SHOP-015: Filters & Sorting
# ---------------------------------------------------------------------------

def test_shop_010_filter_groups_and_facets() -> None:
    """SHOP-010: Search catalog provides filter groups with counts."""
    res = search_catalog_products(query="")
    groups = res.filter_state.available_groups
    assert len(groups) >= 3
    group_names = [g.name for g in groups]
    assert "Category" in group_names
    assert "Brand" in group_names
    assert "Price Range" in group_names


def test_shop_011_active_filter_application() -> None:
    """SHOP-011: Applying category filter exposes removable active filter pills."""
    res = search_catalog_products(query="", category="outerwear")
    active = res.filter_state.active_filters
    assert len(active) == 1
    assert active[0].group_id == "grp-category"
    assert active[0].label == "Outerwear"


def test_shop_012_sort_options_enum() -> None:
    """SHOP-012: Sort options include relevance, newest, and price ascending/descending."""
    assert SortOption.RELEVANCE == "relevance"
    assert SortOption.NEWEST == "newest"
    assert SortOption.PRICE_LOW_HIGH == "price_asc"
    assert SortOption.PRICE_HIGH_LOW == "price_desc"
    assert SortOption.POPULARITY == "popularity"


# ---------------------------------------------------------------------------
# SHOP-020 - SHOP-026: Product Detail & Variants
# ---------------------------------------------------------------------------

def test_shop_020_product_detail_retrieval() -> None:
    """SHOP-020: Product detail retrieves authoritative pricing, gallery, and ratings."""
    prod = get_product_detail("prod-denim-01")
    assert prod is not None
    assert prod.brand == "RawDenim Co."
    assert prod.title == "Selvedge Oversized Denim Jacket"
    assert len(prod.media_gallery) >= 3
    assert prod.price.amount == 4999.0
    assert prod.price.discount_percentage == 28
    assert prod.rating.value == 4.7


def test_shop_021_variant_groups_and_states() -> None:
    """SHOP-021: Variant selector groups enforce sizes, washes, and availability states."""
    prod = get_product_detail("prod-denim-01")
    assert prod is not None
    assert len(prod.variant_groups) == 2

    # Verify color group options
    color_group = next((g for g in prod.variant_groups if g.variant_type == VariantType.COLOR), None)
    assert color_group is not None
    options = {o.value: o.state for o in color_group.options}
    assert options["raw_indigo"] == VariantState.SELECTED
    assert options["faded_black"] == VariantState.UNAVAILABLE


def test_shop_022_delivery_info_and_specifications() -> None:
    """SHOP-022: Delivery estimate and technical specs are provided factually."""
    prod = get_product_detail("prod-denim-01")
    assert prod is not None
    assert prod.delivery_info is not None
    assert prod.delivery_info.is_free_delivery is True
    assert len(prod.specifications) >= 3
    spec_map = {s.name: s.value for s in prod.specifications}
    assert "14oz Japanese Selvedge" in spec_map["Fabric"]


def test_shop_023_complete_the_look_cross_sell() -> None:
    """SHOP-023: Complete the look bridges product to outfit pieces."""
    prod = get_product_detail("prod-denim-01")
    assert prod is not None
    assert len(prod.complete_the_look) >= 1
    slot = prod.complete_the_look[0]
    assert slot.slot_name == "top"
    assert slot.product_id == "prod-linen-02"
    assert slot.price.amount == 2499.0


def test_shop_024_product_detail_template_builder() -> None:
    """SHOP-024: Product detail template includes breadcrumbs and sticky bar config."""
    tpl = get_product_detail_template("prod-denim-01")
    assert tpl.sticky_action_enabled is True
    assert len(tpl.breadcrumb_trail) >= 3
    assert tpl.product.id == "prod-denim-01"


# ---------------------------------------------------------------------------
# SHOP-030 - SHOP-035: Cart & Quantity
# ---------------------------------------------------------------------------

def test_shop_030_get_user_cart() -> None:
    """SHOP-030: Cart retrieves line items and calculates financial subtotal."""
    cart = get_user_cart("cart-user-1")
    assert cart.cart_id == "cart-user-1"
    assert len(cart.items) >= 1
    assert cart.summary.subtotal == 4999.0
    assert cart.summary.total == 4999.0


def test_shop_031_add_item_to_cart() -> None:
    """SHOP-031: Add to cart increments quantity and updates line price."""
    req = AddToCartRequestContract(
        product_id="prod-linen-02",
        quantity=2,
        selected_variants={"size": "M"},
    )
    cart = add_item_to_cart("cart-user-1", req)
    linen_item = next((i for i in cart.items if i.product_id == "prod-linen-02"), None)
    assert linen_item is not None
    assert linen_item.quantity == 2
    assert linen_item.total_price.amount == 4998.0  # 2499 * 2
    assert cart.summary.item_count >= 3


def test_shop_032_update_cart_quantity() -> None:
    """SHOP-032: Update quantity modifies item line total and order summary."""
    update_req = UpdateCartQuantityRequestContract(item_id="cart-item-1", quantity=3)
    cart = update_cart_item_quantity("cart-user-1", update_req)
    item = next((i for i in cart.items if i.item_id == "cart-item-1"), None)
    assert item is not None
    assert item.quantity == 3
    assert item.total_price.amount == 14997.0  # 4999 * 3


def test_shop_033_remove_cart_item_when_quantity_zero() -> None:
    """SHOP-033: Setting quantity to 0 removes line item from cart."""
    # Add a temporary item to remove
    add_item_to_cart(
        "cart-user-1",
        AddToCartRequestContract(product_id="prod-denim-01", quantity=1, selected_variants={"size": "XL"}),
    )
    # Find the newly added item
    cart = get_user_cart("cart-user-1")
    target = next((i for i in cart.items if i.selected_variants.get("size") == "XL"), None)
    assert target is not None

    update_cart_item_quantity("cart-user-1", UpdateCartQuantityRequestContract(item_id=target.item_id, quantity=0))
    updated_cart = get_user_cart("cart-user-1")
    assert not any(i.item_id == target.item_id for i in updated_cart.items)


def test_shop_035_validate_cart_state() -> None:
    """SHOP-035: Pre-checkout validation verifies item stock and readiness."""
    report = validate_cart_state("cart-user-1")
    assert report.is_valid is True
    assert report.has_out_of_stock is False
    assert len(report.messages) >= 1


# ---------------------------------------------------------------------------
# SHOP-040 - SHOP-046: Checkout & Orders
# ---------------------------------------------------------------------------

def test_shop_040_checkout_template() -> None:
    """SHOP-040: Progressive checkout provides addresses, shipping, and payment options."""
    chk = get_checkout_template("chk-101")
    assert chk.screen_id == ShoppingScreenId.SH08_CHECKOUT
    assert chk.checkout_state.is_ready_to_place is True
    assert len(chk.available_addresses) >= 1
    assert len(chk.available_delivery_methods) >= 2
    assert len(chk.available_payment_methods) >= 2


def test_shop_044_order_review_template() -> None:
    """SHOP-044: Order review summarizes address, shipping method, and total payable."""
    rev = get_order_review_template("chk-101")
    assert rev.screen_id == ShoppingScreenId.SH09_ORDER_REVIEW
    assert rev.delivery_address.city == "Mumbai"
    assert rev.delivery_method.name == "Express Courier"
    assert rev.payment_method.method_type == "upi"
    assert rev.summary.total > 0


def test_shop_047_order_confirmation_template() -> None:
    """SHOP-047: Order confirmation exposes generated order number and delivery date."""
    conf = get_confirmation_template("ord-98210")
    assert conf.screen_id == ShoppingScreenId.SH10_ORDER_CONFIRMATION
    assert conf.order_number == "FXS-2026-98210"
    assert "2026" in conf.estimated_delivery
    assert conf.total_amount == 4999.0


def test_shop_050_orders_template() -> None:
    """SHOP-050: Order history lists customer orders with status."""
    orders_tpl = get_orders_template("user-1")
    assert orders_tpl.screen_id == ShoppingScreenId.SH11_ORDERS
    assert orders_tpl.total_orders >= 1
    assert orders_tpl.orders[0].status == OrderStatus.PROCESSING


def test_shop_051_order_detail_template() -> None:
    """SHOP-051: Granular order detail exposes tracking progression steps."""
    detail = get_order_detail_template("ord-98210")
    assert detail.screen_id == ShoppingScreenId.SH12_ORDER_DETAIL
    assert detail.order.order_number == "FXS-2026-98210"
    assert len(detail.tracking_steps) == 4
    assert detail.tracking_steps[0]["step"] == "Order Placed"
    assert detail.tracking_steps[0]["status"] == "completed"


# ---------------------------------------------------------------------------
# SHOP-060: Wishlist & Product Comparison
# ---------------------------------------------------------------------------

def test_shop_060_wishlist_toggle() -> None:
    """SHOP-060: Wishlist toggle updates saved state and item count."""
    res1 = toggle_user_wishlist("user-test-wl", WishlistToggleRequestContract(product_id="prod-denim-01", currently_wishlisted=False))
    assert res1.is_in_wishlist is True
    assert res1.total_wishlist_count == 1
    assert "saved to wishlist" in res1.message

    res2 = toggle_user_wishlist("user-test-wl", WishlistToggleRequestContract(product_id="prod-denim-01", currently_wishlisted=True))
    assert res2.is_in_wishlist is False
    assert res2.total_wishlist_count == 0
    assert "removed from wishlist" in res2.message


def test_shop_061_product_comparison_matrix() -> None:
    """SHOP-061: Compare products builds attribute matrix across specified items."""
    cmp = compare_products(["prod-denim-01", "prod-linen-02"])
    assert len(cmp.product_ids) == 2
    assert len(cmp.attributes) == 3
    attr_names = [a.attribute_name for a in cmp.attributes]
    assert "Price" in attr_names
    assert "Availability" in attr_names
    assert "Rating" in attr_names
