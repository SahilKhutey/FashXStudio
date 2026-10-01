"""Shopping UI System & Commerce Experience Domain Service — Phase 07.

Provides domain models, in-memory fixtures, state machine transitions, and
template builders for the complete FashXStudio shopping experience.
"""

from typing import Any
from schemas.visual.components import PriceSpecContract, RatingSpecContract
from schemas.visual.shopping import (
    ActiveFilterContract,
    AddToCartRequestContract,
    CartContract,
    CartItemContract,
    CartSummaryContract,
    CartTemplateSpecContract,
    CartValidationResultContract,
    CategoryTemplateSpecContract,
    CheckoutStateContract,
    CheckoutStep,
    CheckoutSubmitRequestContract,
    CheckoutTemplateSpecContract,
    ComparisonAttributeContract,
    CompleteTheLookSlotContract,
    ConfirmationTemplateSpecContract,
    DeliveryAddressContract,
    DeliveryInfoContract,
    DeliveryMethodContract,
    FilterGroupContract,
    FilterOptionContract,
    FilterStateContract,
    FilterType,
    OrderDetailTemplateSpecContract,
    OrderContract,
    OrderItemContract,
    OrderReviewTemplateSpecContract,
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
    WishlistTemplateSpecContract,
    WishlistToggleRequestContract,
    WishlistToggleResultContract,
)


# ---------------------------------------------------------------------------
# In-Memory Domain Fixtures (Sections 7.6 - 7.30)
# ---------------------------------------------------------------------------

SAMPLE_PRODUCT_DETAILS: dict[str, ShoppingProductDetailContract] = {
    "prod-denim-01": ShoppingProductDetailContract(
        id="prod-denim-01",
        brand="RawDenim Co.",
        title="Selvedge Oversized Denim Jacket",
        primary_media_uri="https://images.fashx.com/products/denim_jacket_front.jpg",
        media_gallery=[
            "https://images.fashx.com/products/denim_jacket_front.jpg",
            "https://images.fashx.com/products/denim_jacket_back.jpg",
            "https://images.fashx.com/products/denim_jacket_detail.jpg",
        ],
        price=PriceSpecContract(amount=4999.0, original_amount=6999.0, discount_percentage=28),
        availability=ProductAvailabilityState.IN_STOCK,
        stock_count=18,
        description="Crafted on vintage shuttle looms using 14oz Japanese selvedge denim. Boxy, relaxed fit tailored for all seasons.",
        rating=RatingSpecContract(value=4.7, rating_count=142),
        variant_groups=[
            ProductVariantGroupContract(
                id="var-color-denim",
                variant_type=VariantType.COLOR,
                title="Washes",
                options=[
                    ProductVariantOptionContract(id="opt-raw-indigo", variant_type=VariantType.COLOR, value="raw_indigo", label="Raw Indigo", state=VariantState.SELECTED, swatch_hex="#1a2744"),
                    ProductVariantOptionContract(id="opt-washed-blue", variant_type=VariantType.COLOR, value="washed_blue", label="Washed Blue", state=VariantState.AVAILABLE, swatch_hex="#4b6b94"),
                    ProductVariantOptionContract(id="opt-faded-black", variant_type=VariantType.COLOR, value="faded_black", label="Faded Black", state=VariantState.UNAVAILABLE, swatch_hex="#222222"),
                ],
            ),
            ProductVariantGroupContract(
                id="var-size-denim",
                variant_type=VariantType.SIZE,
                title="Sizes",
                options=[
                    ProductVariantOptionContract(id="opt-s", variant_type=VariantType.SIZE, value="S", label="S", state=VariantState.AVAILABLE),
                    ProductVariantOptionContract(id="opt-m", variant_type=VariantType.SIZE, value="M", label="M", state=VariantState.SELECTED),
                    ProductVariantOptionContract(id="opt-l", variant_type=VariantType.SIZE, value="L", label="L", state=VariantState.AVAILABLE),
                    ProductVariantOptionContract(id="opt-xl", variant_type=VariantType.SIZE, value="XL", label="XL", state=VariantState.AVAILABLE),
                    ProductVariantOptionContract(id="opt-xxl", variant_type=VariantType.SIZE, value="XXL", label="XXL", state=VariantState.UNAVAILABLE),
                ],
            ),
        ],
        delivery_info=DeliveryInfoContract(
            estimated_delivery_days="2-3 Business Days",
            shipping_fee=0.0,
            is_free_delivery=True,
            postal_code="400001",
        ),
        specifications=[
            SpecificationAttributeContract(name="Fabric", value="100% Cotton (14oz Japanese Selvedge)"),
            SpecificationAttributeContract(name="Fit", value="Relaxed Boxy Fit"),
            SpecificationAttributeContract(name="Care", value="Machine wash cold inside out, hang dry"),
            SpecificationAttributeContract(name="Origin", value="Kojima, Okayama Prefecture"),
        ],
        complete_the_look=[
            CompleteTheLookSlotContract(
                slot_name="top",
                product_id="prod-linen-02",
                product_title="Relaxed Camp Collar Linen Shirt",
                price=PriceSpecContract(amount=2499.0),
                media_uri="https://images.fashx.com/products/linen_shirt_sand.jpg",
            ),
        ],
        related_product_ids=["prod-linen-02"],
        is_in_wishlist=False,
    ),
    "prod-linen-02": ShoppingProductDetailContract(
        id="prod-linen-02",
        brand="Breeze & Loom",
        title="Relaxed Camp Collar Linen Shirt",
        primary_media_uri="https://images.fashx.com/products/linen_shirt_sand.jpg",
        media_gallery=[
            "https://images.fashx.com/products/linen_shirt_sand.jpg",
            "https://images.fashx.com/products/linen_shirt_model.jpg",
        ],
        price=PriceSpecContract(amount=2499.0),
        availability=ProductAvailabilityState.IN_STOCK,
        stock_count=45,
        description="Airy, breathable Cuban collar shirt woven from 100% pure Normandy flax.",
        rating=RatingSpecContract(value=4.5, rating_count=88),
        variant_groups=[
            ProductVariantGroupContract(
                id="var-size-linen",
                variant_type=VariantType.SIZE,
                title="Sizes",
                options=[
                    ProductVariantOptionContract(id="opt-linen-s", variant_type=VariantType.SIZE, value="S", label="S", state=VariantState.AVAILABLE),
                    ProductVariantOptionContract(id="opt-linen-m", variant_type=VariantType.SIZE, value="M", label="M", state=VariantState.SELECTED),
                    ProductVariantOptionContract(id="opt-linen-l", variant_type=VariantType.SIZE, value="L", label="L", state=VariantState.AVAILABLE),
                ],
            ),
        ],
        delivery_info=DeliveryInfoContract(
            estimated_delivery_days="3-4 Business Days",
            shipping_fee=150.0,
            is_free_delivery=False,
        ),
        specifications=[
            SpecificationAttributeContract(name="Material", value="100% French Flax Linen"),
            SpecificationAttributeContract(name="Collar", value="Camp / Cuban Collar"),
        ],
        complete_the_look=[],
        related_product_ids=["prod-denim-01"],
        is_in_wishlist=True,
    ),
}

SAMPLE_FILTER_GROUPS: list[FilterGroupContract] = [
    FilterGroupContract(
        id="grp-category",
        name="Category",
        filter_type=FilterType.CHECKBOX,
        options=[
            FilterOptionContract(id="cat-outerwear", label="Outerwear", value="outerwear", count=18),
            FilterOptionContract(id="cat-tops", label="Tops & Shirts", value="tops", count=45),
            FilterOptionContract(id="cat-bottoms", label="Trousers & Denims", value="bottoms", count=32),
            FilterOptionContract(id="cat-footwear", label="Footwear", value="shoes", count=14),
        ],
    ),
    FilterGroupContract(
        id="grp-brand",
        name="Brand",
        filter_type=FilterType.CHECKBOX,
        options=[
            FilterOptionContract(id="brd-rawdenim", label="RawDenim Co.", value="rawdenim", count=24),
            FilterOptionContract(id="brd-breeze", label="Breeze & Loom", value="breeze", count=16),
            FilterOptionContract(id="brd-luxe", label="Luxe Atelier", value="luxe", count=19),
        ],
    ),
    FilterGroupContract(
        id="grp-price",
        name="Price Range",
        filter_type=FilterType.RANGE,
        options=[
            FilterOptionContract(id="prc-under2500", label="Under ₹2,500", value="0-2500", count=28),
            FilterOptionContract(id="prc-2500-5000", label="₹2,500 - ₹5,000", value="2500-5000", count=41),
            FilterOptionContract(id="prc-above5000", label="Above ₹5,000", value="5000+", count=15),
        ],
    ),
]

SAMPLE_CART_STORE: dict[str, CartContract] = {
    "cart-user-1": CartContract(
        cart_id="cart-user-1",
        items=[
            CartItemContract(
                item_id="cart-item-1",
                product_id="prod-denim-01",
                title="Selvedge Oversized Denim Jacket",
                brand="RawDenim Co.",
                media_uri="https://images.fashx.com/products/denim_jacket_front.jpg",
                selected_variants={"color": "raw_indigo", "size": "M"},
                quantity=1,
                unit_price=PriceSpecContract(amount=4999.0),
                total_price=PriceSpecContract(amount=4999.0),
                availability=ProductAvailabilityState.IN_STOCK,
            ),
        ],
        summary=CartSummaryContract(
            subtotal=4999.0,
            discount=0.0,
            delivery_fee=0.0,
            total=4999.0,
            currency_symbol="₹",
            item_count=1,
        ),
        state=ShoppingState.READY,
        validation_errors=[],
    )
}

SAMPLE_WISHLIST_STORE: dict[str, WishlistContract] = {
    "user-1": WishlistContract(
        wishlist_id="wl-user-1",
        user_id="user-1",
        items=[
            WishlistItemContract(
                item_id="wl-item-1",
                product_id="prod-linen-02",
                title="Relaxed Camp Collar Linen Shirt",
                brand="Breeze & Loom",
                media_uri="https://images.fashx.com/products/linen_shirt_sand.jpg",
                price=PriceSpecContract(amount=2499.0),
                availability=ProductAvailabilityState.IN_STOCK,
                added_timestamp="2026-09-30T10:15:00Z",
            ),
        ],
        total_count=1,
    )
}

SAMPLE_ADDRESSES: list[DeliveryAddressContract] = [
    DeliveryAddressContract(
        id="addr-default",
        full_name="Sahil Khutey",
        address_line1="B-402, Sea Green Apartments, Bandra West",
        city="Mumbai",
        state="Maharashtra",
        postal_code="400050",
        country="India",
        phone="+91 98765 43210",
        is_default=True,
    ),
]

SAMPLE_DELIVERY_METHODS: list[DeliveryMethodContract] = [
    DeliveryMethodContract(
        id="del-express",
        name="Express Courier",
        description="Air express delivery via BlueDart / Delhivery",
        fee=0.0,
        estimated_time="1-2 Business Days",
    ),
    DeliveryMethodContract(
        id="del-standard",
        name="Standard Ground",
        description="Surface transport with carbon-neutral shipping",
        fee=0.0,
        estimated_time="3-5 Business Days",
    ),
]

SAMPLE_PAYMENT_METHODS: list[PaymentMethodContract] = [
    PaymentMethodContract(
        id="pay-upi",
        method_type="upi",
        title="UPI Instant (Google Pay, PhonePe, Paytm)",
        is_selected=True,
    ),
    PaymentMethodContract(
        id="pay-card",
        method_type="card",
        title="HDFC Regalia Credit Card",
        last4="4821",
        is_selected=False,
    ),
]

SAMPLE_ORDERS: list[OrderContract] = [
    OrderContract(
        order_id="ord-98210",
        order_number="FXS-2026-98210",
        placed_at="2026-09-29T14:32:00Z",
        status=OrderStatus.PROCESSING,
        items=[
            OrderItemContract(
                product_id="prod-denim-01",
                title="Selvedge Oversized Denim Jacket",
                brand="RawDenim Co.",
                media_uri="https://images.fashx.com/products/denim_jacket_front.jpg",
                selected_variants={"size": "M"},
                quantity=1,
                unit_price=PriceSpecContract(amount=4999.0),
                total_price=PriceSpecContract(amount=4999.0),
            ),
        ],
        delivery_address=SAMPLE_ADDRESSES[0],
        delivery_method=SAMPLE_DELIVERY_METHODS[0],
        payment_summary="UPI ID: sahil@okaxis",
        price_summary=CartSummaryContract(
            subtotal=4999.0,
            discount=0.0,
            delivery_fee=0.0,
            total=4999.0,
            currency_symbol="₹",
            item_count=1,
        ),
    ),
]


# ---------------------------------------------------------------------------
# Domain Service Implementation (Sections 7.1 - 7.50)
# ---------------------------------------------------------------------------

def get_product_detail(product_id: str) -> ShoppingProductDetailContract | None:
    """Lookup authoritative product detail by ID (Section 7.21)."""
    return SAMPLE_PRODUCT_DETAILS.get(product_id)


def search_catalog_products(
    query: str = "",
    category: str | None = None,
    sort_option: SortOption = SortOption.RELEVANCE,
) -> SearchResultsTemplateSpecContract:
    """Execute catalog search and facet generation (Section 7.19 & 7.20)."""
    product_ids = list(SAMPLE_PRODUCT_DETAILS.keys())
    if query:
        q_lower = query.lower()
        product_ids = [
            pid for pid, prod in SAMPLE_PRODUCT_DETAILS.items()
            if q_lower in prod.title.lower() or q_lower in prod.brand.lower()
        ]

    active_filters: list[ActiveFilterContract] = []
    if category:
        active_filters.append(ActiveFilterContract(group_id="grp-category", option_id=f"cat-{category}", label=category.capitalize()))

    filter_state = FilterStateContract(
        available_groups=SAMPLE_FILTER_GROUPS,
        active_filters=active_filters,
        total_matches=len(product_ids),
    )

    return SearchResultsTemplateSpecContract(
        query=query,
        total_results=len(product_ids),
        suggestions=["Linen shirts", "Selvedge denim", "Summer jackets"] if not product_ids else [],
        filter_state=filter_state,
        product_ids=product_ids,
    )


def compare_products(product_ids: list[str]) -> ProductComparisonContract:
    """Generate side-by-side product comparison matrix (Section 7.60)."""
    products = [SAMPLE_PRODUCT_DETAILS[pid] for pid in product_ids if pid in SAMPLE_PRODUCT_DETAILS]
    price_values = {p.id: f"{p.price.currency_symbol}{p.price.amount:,.0f}" for p in products}
    avail_values = {p.id: str(p.availability).replace("_", " ").title() for p in products}
    rating_values = {p.id: f"{p.rating.value}★ ({p.rating.rating_count})" if p.rating else "N/A" for p in products}

    attributes = [
        ComparisonAttributeContract(attribute_name="Price", product_values=price_values),
        ComparisonAttributeContract(attribute_name="Availability", product_values=avail_values),
        ComparisonAttributeContract(attribute_name="Rating", product_values=rating_values),
    ]

    return ProductComparisonContract(product_ids=[p.id for p in products], attributes=attributes)


def get_user_cart(cart_id: str = "cart-user-1") -> CartContract:
    """Retrieve active user cart or create a fresh empty cart (Section 7.36)."""
    if cart_id not in SAMPLE_CART_STORE:
        SAMPLE_CART_STORE[cart_id] = CartContract(
            cart_id=cart_id,
            items=[],
            summary=CartSummaryContract(subtotal=0.0, total=0.0, item_count=0),
            state=ShoppingState.EMPTY,
        )
    return SAMPLE_CART_STORE[cart_id]


def add_item_to_cart(cart_id: str, payload: AddToCartRequestContract) -> CartContract:
    """Add product variant to cart and recalculate totals (Section 7.31)."""
    cart = get_user_cart(cart_id)
    product = SAMPLE_PRODUCT_DETAILS.get(payload.product_id)
    if not product:
        raise ValueError(f"Product '{payload.product_id}' does not exist.")

    if product.availability == ProductAvailabilityState.OUT_OF_STOCK:
        raise ValueError(f"Cannot add out of stock product '{product.title}'.")

    # Check if identical item (id + variants) exists in cart
    existing = next(
        (
            item for item in cart.items
            if item.product_id == payload.product_id and item.selected_variants == payload.selected_variants
        ),
        None,
    )

    if existing:
        new_qty = min(existing.quantity + payload.quantity, 10)
        existing.quantity = new_qty
        existing.total_price = PriceSpecContract(amount=existing.unit_price.amount * new_qty)
    else:
        new_item = CartItemContract(
            item_id=f"cart-item-{len(cart.items) + 1}",
            product_id=product.id,
            title=product.title,
            brand=product.brand,
            media_uri=product.primary_media_uri,
            selected_variants=payload.selected_variants,
            quantity=payload.quantity,
            unit_price=product.price,
            total_price=PriceSpecContract(amount=product.price.amount * payload.quantity),
            availability=product.availability,
        )
        cart.items.append(new_item)

    # Recalculate summary
    subtotal = sum(i.total_price.amount for i in cart.items)
    cart.summary = CartSummaryContract(
        subtotal=subtotal,
        discount=0.0,
        delivery_fee=0.0 if subtotal > 1000 else 150.0,
        total=subtotal,
        currency_symbol="₹",
        item_count=sum(i.quantity for i in cart.items),
    )
    cart.state = ShoppingState.READY
    return cart


def update_cart_item_quantity(cart_id: str, payload: UpdateCartQuantityRequestContract) -> CartContract:
    """Increment, decrement, or remove item from cart (Section 7.39)."""
    cart = get_user_cart(cart_id)
    target = next((i for i in cart.items if i.item_id == payload.item_id), None)
    if not target:
        raise ValueError(f"Cart item '{payload.item_id}' not found.")

    if payload.quantity <= 0:
        cart.items = [i for i in cart.items if i.item_id != payload.item_id]
    else:
        target.quantity = payload.quantity
        target.total_price = PriceSpecContract(amount=target.unit_price.amount * payload.quantity)

    subtotal = sum(i.total_price.amount for i in cart.items)
    cart.summary = CartSummaryContract(
        subtotal=subtotal,
        discount=0.0,
        delivery_fee=0.0 if subtotal > 1000 or not cart.items else 150.0,
        total=subtotal,
        currency_symbol="₹",
        item_count=sum(i.quantity for i in cart.items),
    )
    cart.state = ShoppingState.READY if cart.items else ShoppingState.EMPTY
    return cart


def validate_cart_state(cart_id: str) -> CartValidationResultContract:
    """Validate cart items, availability, and pricing before checkout (Section 7.40)."""
    cart = get_user_cart(cart_id)
    if not cart.items:
        return CartValidationResultContract(is_valid=False, messages=["Cart is empty."])

    messages: list[str] = []
    has_out_of_stock = False

    for item in cart.items:
        prod = SAMPLE_PRODUCT_DETAILS.get(item.product_id)
        if prod and prod.availability == ProductAvailabilityState.OUT_OF_STOCK:
            has_out_of_stock = True
            messages.append(f"Item '{item.title}' is currently out of stock.")

    return CartValidationResultContract(
        is_valid=not has_out_of_stock,
        has_out_of_stock=has_out_of_stock,
        messages=messages if messages else ["Cart is verified and ready for checkout."],
    )


def toggle_user_wishlist(user_id: str, payload: WishlistToggleRequestContract) -> WishlistToggleResultContract:
    """Toggle wishlist state for product with optimistic response (Section 7.33)."""
    if user_id not in SAMPLE_WISHLIST_STORE:
        SAMPLE_WISHLIST_STORE[user_id] = WishlistContract(wishlist_id=f"wl-{user_id}", user_id=user_id, items=[])

    wl = SAMPLE_WISHLIST_STORE[user_id]
    is_saved = not payload.currently_wishlisted

    if is_saved:
        prod = SAMPLE_PRODUCT_DETAILS.get(payload.product_id)
        if prod:
            wl.items.append(
                WishlistItemContract(
                    item_id=f"wl-item-{len(wl.items) + 1}",
                    product_id=prod.id,
                    title=prod.title,
                    brand=prod.brand,
                    media_uri=prod.primary_media_uri,
                    price=prod.price,
                    availability=prod.availability,
                    added_timestamp="2026-10-01T11:00:00Z",
                )
            )
    else:
        wl.items = [i for i in wl.items if i.product_id != payload.product_id]

    wl.total_count = len(wl.items)

    return WishlistToggleResultContract(
        product_id=payload.product_id,
        is_in_wishlist=is_saved,
        total_wishlist_count=wl.total_count,
        message=f"Product {'saved to wishlist' if is_saved else 'removed from wishlist'}.",
    )


# ---------------------------------------------------------------------------
# Template Builders (Sections 7.4, 7.6 - 7.50, 7.70)
# ---------------------------------------------------------------------------

def get_shopping_home_template() -> ShoppingHomeTemplateSpecContract:
    """Build SH01 Shopping Home template spec (Section 7.6)."""
    return ShoppingHomeTemplateSpecContract(
        screen_id=ShoppingScreenId.SH01_SHOPPING_HOME,
        search_placeholder="Search 14oz Japanese selvedge, linen shirts, leather sneakers...",
        featured_collection_ids=["coll-monsoon-26"],
        categories=[
            {"id": "outerwear", "name": "Outerwear", "image_uri": "https://images.fashx.com/cat/outerwear.jpg"},
            {"id": "tops", "name": "Tops & Shirts", "image_uri": "https://images.fashx.com/cat/tops.jpg"},
            {"id": "bottoms", "name": "Trousers & Denims", "image_uri": "https://images.fashx.com/cat/bottoms.jpg"},
        ],
        trending_product_ids=list(SAMPLE_PRODUCT_DETAILS.keys()),
        recommended_product_ids=list(SAMPLE_PRODUCT_DETAILS.keys()),
    )


def get_category_template(category_id: str) -> CategoryTemplateSpecContract:
    """Build SH02 Category template spec (Section 7.7)."""
    return CategoryTemplateSpecContract(
        screen_id=ShoppingScreenId.SH02_CATEGORY,
        category_id=category_id,
        category_name=category_id.capitalize(),
        parent_category_name="Fashion & Apparel",
        subcategories=[
            {"id": f"{category_id}-jackets", "name": "Jackets & Overshirts"},
            {"id": f"{category_id}-coats", "name": "Overcoats"},
        ],
        featured_product_ids=list(SAMPLE_PRODUCT_DETAILS.keys()),
    )


def get_product_detail_template(product_id: str) -> ProductDetailTemplateSpecContract:
    """Build SH07-adjacent Product Detail template spec (Section 7.21)."""
    product = get_product_detail(product_id)
    if not product:
        raise ValueError(f"Product '{product_id}' not found.")
    return ProductDetailTemplateSpecContract(
        product=product,
        breadcrumb_trail=["Shopping", "Outerwear", product.brand, product.title],
        sticky_action_enabled=True,
    )


def get_wishlist_template(user_id: str = "user-1") -> WishlistTemplateSpecContract:
    """Build SH05 Wishlist template spec (Section 7.33)."""
    wl = SAMPLE_WISHLIST_STORE.get(user_id, WishlistContract(wishlist_id=f"wl-{user_id}", user_id=user_id, items=[]))
    return WishlistTemplateSpecContract(
        screen_id=ShoppingScreenId.SH05_WISHLIST,
        wishlist=wl,
        sort_options=["Recently Added", "Price: Low to High", "Price: High to Low"],
    )


def get_cart_template(cart_id: str = "cart-user-1") -> CartTemplateSpecContract:
    """Build SH06 Cart template spec (Section 7.36)."""
    cart = get_user_cart(cart_id)
    return CartTemplateSpecContract(
        screen_id=ShoppingScreenId.SH06_CART,
        cart=cart,
        suggested_cross_sell_ids=["prod-linen-02"],
    )


def get_checkout_template(checkout_id: str = "chk-101") -> CheckoutTemplateSpecContract:
    """Build SH08 Progressive Checkout template spec (Section 7.41)."""
    cart = get_user_cart("cart-user-1")
    checkout_state = CheckoutStateContract(
        checkout_id=checkout_id,
        current_step=CheckoutStep.CONTACT,
        cart=cart,
        delivery_address=SAMPLE_ADDRESSES[0],
        delivery_method=SAMPLE_DELIVERY_METHODS[0],
        payment_method=SAMPLE_PAYMENT_METHODS[0],
        is_ready_to_place=True,
    )
    return CheckoutTemplateSpecContract(
        screen_id=ShoppingScreenId.SH08_CHECKOUT,
        checkout_state=checkout_state,
        available_addresses=SAMPLE_ADDRESSES,
        available_delivery_methods=SAMPLE_DELIVERY_METHODS,
        available_payment_methods=SAMPLE_PAYMENT_METHODS,
    )


def get_order_review_template(checkout_id: str = "chk-101") -> OrderReviewTemplateSpecContract:
    """Build SH09 Order Review template spec (Section 7.45)."""
    cart = get_user_cart("cart-user-1")
    return OrderReviewTemplateSpecContract(
        screen_id=ShoppingScreenId.SH09_ORDER_REVIEW,
        checkout_id=checkout_id,
        items=cart.items,
        delivery_address=SAMPLE_ADDRESSES[0],
        delivery_method=SAMPLE_DELIVERY_METHODS[0],
        payment_method=SAMPLE_PAYMENT_METHODS[0],
        summary=cart.summary,
    )


def get_confirmation_template(order_id: str = "ord-98210") -> ConfirmationTemplateSpecContract:
    """Build SH10 Order Confirmation template spec (Section 7.47)."""
    order = next((o for o in SAMPLE_ORDERS if o.order_id == order_id), SAMPLE_ORDERS[0])
    return ConfirmationTemplateSpecContract(
        screen_id=ShoppingScreenId.SH10_ORDER_CONFIRMATION,
        order_number=order.order_number,
        order_id=order.order_id,
        placed_at=order.placed_at,
        estimated_delivery="October 4, 2026",
        items_count=len(order.items),
        total_amount=order.price_summary.total,
        currency_symbol=order.price_summary.currency_symbol,
    )


def get_orders_template(user_id: str = "user-1") -> OrdersTemplateSpecContract:
    """Build SH11 Order History list template spec (Section 7.48)."""
    return OrdersTemplateSpecContract(
        screen_id=ShoppingScreenId.SH11_ORDERS,
        orders=SAMPLE_ORDERS,
        total_orders=len(SAMPLE_ORDERS),
    )


def get_order_detail_template(order_id: str) -> OrderDetailTemplateSpecContract:
    """Build SH12 Granular Order Detail template spec (Section 7.50)."""
    order = next((o for o in SAMPLE_ORDERS if o.order_id == order_id), None)
    if not order:
        raise ValueError(f"Order '{order_id}' not found.")
    return OrderDetailTemplateSpecContract(
        screen_id=ShoppingScreenId.SH12_ORDER_DETAIL,
        order=order,
        tracking_steps=[
            {"step": "Order Placed", "status": "completed", "time": "29 Sep 2026, 14:32"},
            {"step": "Processing & Verification", "status": "current", "time": "30 Sep 2026, 09:15"},
            {"step": "Dispatched via Express Courier", "status": "pending", "time": "Est. 02 Oct 2026"},
            {"step": "Delivered", "status": "pending", "time": "Est. 04 Oct 2026"},
        ],
    )
