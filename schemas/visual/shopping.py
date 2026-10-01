"""FashXStudio Shopping UI System & Commerce Experience Contracts — Phase 07.

Defines Pydantic v2 data contracts for the Shopping UI System (Sections 7.1-7.83):
- Catalog & Listing: ProductGrid, Category, ResultSummary, Filters, Sort
- Product Detail: ProductGallery, VariantSelector, Availability, Delivery, Complete-the-Look
- Cart & Wishlist: CartItem, CartSummary, CartValidation, WishlistItem
- Checkout & Orders: Multi-step checkout, OrderReview, OrderConfirmation, OrderDetail
- 12 Shopping Templates: SH01-SH12 Template Specifications

All schemas enforce extra="forbid" via BaseContractModel (Constitution Rule I02).
"""

from enum import StrEnum
from typing import Any
from pydantic import Field
from schemas.base import BaseContractModel
from schemas.visual.components import PriceSpecContract, RatingSpecContract


# ---------------------------------------------------------------------------
# Enums (Sections 7.18, 7.26, 7.30, 7.49, 7.51)
# ---------------------------------------------------------------------------

class ProductAvailabilityState(StrEnum):
    """Product stock and fulfillment state (Section 7.30)."""
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    UNAVAILABLE = "unavailable"
    PREORDER = "preorder"


class VariantType(StrEnum):
    """Product variant attribute dimensions (Section 7.25)."""
    SIZE = "size"
    COLOR = "color"
    MATERIAL = "material"
    STYLE = "style"


class VariantState(StrEnum):
    """Variant selection and availability state (Section 7.26)."""
    AVAILABLE = "available"
    SELECTED = "selected"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"
    LOADING = "loading"


class SortOption(StrEnum):
    """Authoritative catalog sort orders (Section 7.18)."""
    RELEVANCE = "relevance"
    NEWEST = "newest"
    PRICE_LOW_HIGH = "price_asc"
    PRICE_HIGH_LOW = "price_desc"
    POPULARITY = "popularity"


class FilterType(StrEnum):
    """Filter group input display type (Section 7.13 & 7.14)."""
    CHECKBOX = "checkbox"
    RADIO = "radio"
    RANGE = "range"
    SWATCH = "swatch"


class ShoppingState(StrEnum):
    """Unified shopping visual state machine (Section 7.51)."""
    LOADING = "loading"
    READY = "ready"
    EMPTY = "empty"
    PARTIAL = "partial"
    VALIDATION_ERROR = "validation_error"
    SERVICE_ERROR = "service_error"
    UNAVAILABLE = "unavailable"
    SUCCESS = "success"


class OrderStatus(StrEnum):
    """Authoritative commerce order lifecycle status (Section 7.49)."""
    PLACED = "placed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    REFUNDED = "refunded"


class CheckoutStep(StrEnum):
    """Progressive checkout step model (Section 7.43)."""
    CONTACT = "contact"
    ADDRESS = "address"
    DELIVERY = "delivery"
    PAYMENT = "payment"
    REVIEW = "review"
    CONFIRMATION = "confirmation"


class ShoppingScreenId(StrEnum):
    """Inventory screen identifiers for Phase-1 shopping (Section 7.3)."""
    SH01_SHOPPING_HOME = "SH01"
    SH02_CATEGORY = "SH02"
    SH03_FILTER = "SH03"
    SH04_SORT = "SH04"
    SH05_WISHLIST = "SH05"
    SH06_CART = "SH06"
    SH07_CART_DETAIL = "SH07"
    SH08_CHECKOUT = "SH08"
    SH09_ORDER_REVIEW = "SH09"
    SH10_ORDER_CONFIRMATION = "SH10"
    SH11_ORDERS = "SH11"
    SH12_ORDER_DETAIL = "SH12"


# ---------------------------------------------------------------------------
# Filter & Sort Contracts (Sections 7.13 - 7.18)
# ---------------------------------------------------------------------------

class FilterOptionContract(BaseContractModel):
    """Single selectable filter dimension option (Section 7.13)."""
    id: str
    label: str
    value: str
    count: int = Field(default=0, ge=0)
    is_selected: bool = Field(default=False)


class FilterGroupContract(BaseContractModel):
    """Grouped catalog filter facet (Section 7.14)."""
    id: str
    name: str
    filter_type: FilterType = Field(default=FilterType.CHECKBOX)
    options: list[FilterOptionContract] = Field(default_factory=list)


class ActiveFilterContract(BaseContractModel):
    """Removable active filter pill representation (Section 7.16)."""
    group_id: str
    option_id: str
    label: str


class FilterStateContract(BaseContractModel):
    """Complete filter facet system state (Section 7.17)."""
    available_groups: list[FilterGroupContract] = Field(default_factory=list)
    active_filters: list[ActiveFilterContract] = Field(default_factory=list)
    total_matches: int = Field(default=0, ge=0)


# ---------------------------------------------------------------------------
# Product & Variant Contracts (Sections 7.21 - 7.30)
# ---------------------------------------------------------------------------

class ProductVariantOptionContract(BaseContractModel):
    """Individual variant choice within a dimension (Section 7.25)."""
    id: str
    variant_type: VariantType
    value: str
    label: str
    state: VariantState = Field(default=VariantState.AVAILABLE)
    swatch_hex: str | None = Field(default=None)
    price_delta: float | None = Field(default=None)


class ProductVariantGroupContract(BaseContractModel):
    """Group of variant choices for a dimension (Section 7.25)."""
    id: str
    variant_type: VariantType
    title: str
    options: list[ProductVariantOptionContract] = Field(default_factory=list)


class DeliveryInfoContract(BaseContractModel):
    """Authoritative delivery estimate and cost breakdown (Section 7.21)."""
    estimated_delivery_days: str
    shipping_fee: float = Field(default=0.0, ge=0.0)
    is_free_delivery: bool = Field(default=False)
    postal_code: str | None = Field(default=None)


class SpecificationAttributeContract(BaseContractModel):
    """Key-value technical or fabric specification (Section 7.21)."""
    name: str
    value: str
    category: str | None = Field(default=None)


class CompleteTheLookSlotContract(BaseContractModel):
    """Fashion-to-shopping cross-linking constituent piece (Section 7.62)."""
    slot_name: str
    product_id: str
    product_title: str
    price: PriceSpecContract
    media_uri: str


class ComparisonAttributeContract(BaseContractModel):
    """Attribute comparison row across multiple products (Section 7.60)."""
    attribute_name: str
    product_values: dict[str, str] = Field(default_factory=dict)


class ProductComparisonContract(BaseContractModel):
    """Data-driven side-by-side product comparison (Section 7.60)."""
    product_ids: list[str] = Field(default_factory=list)
    attributes: list[ComparisonAttributeContract] = Field(default_factory=list)


class ShoppingProductDetailContract(BaseContractModel):
    """Comprehensive product detail visual specification (Section 7.21)."""
    id: str
    brand: str
    title: str
    primary_media_uri: str
    media_gallery: list[str] = Field(default_factory=list)
    price: PriceSpecContract
    availability: ProductAvailabilityState = Field(default=ProductAvailabilityState.IN_STOCK)
    stock_count: int | None = Field(default=None, ge=0)
    description: str
    rating: RatingSpecContract | None = Field(default=None)
    variant_groups: list[ProductVariantGroupContract] = Field(default_factory=list)
    delivery_info: DeliveryInfoContract | None = Field(default=None)
    specifications: list[SpecificationAttributeContract] = Field(default_factory=list)
    complete_the_look: list[CompleteTheLookSlotContract] = Field(default_factory=list)
    related_product_ids: list[str] = Field(default_factory=list)
    is_in_wishlist: bool = Field(default=False)


# ---------------------------------------------------------------------------
# Cart & Wishlist Contracts (Sections 7.33 - 7.40)
# ---------------------------------------------------------------------------

class CartItemContract(BaseContractModel):
    """Cart item with variant selection, quantity, and line price (Section 7.36)."""
    item_id: str
    product_id: str
    title: str
    brand: str
    media_uri: str
    selected_variants: dict[str, str] = Field(default_factory=dict)
    quantity: int = Field(default=1, ge=1, le=10)
    unit_price: PriceSpecContract
    total_price: PriceSpecContract
    availability: ProductAvailabilityState = Field(default=ProductAvailabilityState.IN_STOCK)


class CartSummaryContract(BaseContractModel):
    """Authoritative order financial breakdown (Section 7.37)."""
    subtotal: float = Field(default=0.0, ge=0.0)
    discount: float = Field(default=0.0, ge=0.0)
    delivery_fee: float = Field(default=0.0, ge=0.0)
    total: float = Field(default=0.0, ge=0.0)
    currency_symbol: str = Field(default="₹")
    item_count: int = Field(default=0, ge=0)


class CartContract(BaseContractModel):
    """Active shopping cart state (Section 7.36)."""
    cart_id: str
    items: list[CartItemContract] = Field(default_factory=list)
    summary: CartSummaryContract
    state: ShoppingState = Field(default=ShoppingState.READY)
    validation_errors: list[str] = Field(default_factory=list)


class CartValidationResultContract(BaseContractModel):
    """Pre-checkout cart validation report (Section 7.40)."""
    is_valid: bool
    has_price_change: bool = Field(default=False)
    has_out_of_stock: bool = Field(default=False)
    messages: list[str] = Field(default_factory=list)


class WishlistItemContract(BaseContractModel):
    """Saved product item within user's wishlist (Section 7.33)."""
    item_id: str
    product_id: str
    title: str
    brand: str
    media_uri: str
    price: PriceSpecContract
    availability: ProductAvailabilityState = Field(default=ProductAvailabilityState.IN_STOCK)
    added_timestamp: str


class WishlistContract(BaseContractModel):
    """Complete wishlist representation (Section 7.33)."""
    wishlist_id: str
    user_id: str
    items: list[WishlistItemContract] = Field(default_factory=list)
    total_count: int = Field(default=0, ge=0)


# ---------------------------------------------------------------------------
# Checkout & Orders Contracts (Sections 7.41 - 7.50)
# ---------------------------------------------------------------------------

class DeliveryAddressContract(BaseContractModel):
    """Customer delivery address specification (Section 7.41)."""
    id: str
    full_name: str
    address_line1: str
    address_line2: str | None = Field(default=None)
    city: str
    state: str
    postal_code: str
    country: str = Field(default="India")
    phone: str
    is_default: bool = Field(default=False)


class DeliveryMethodContract(BaseContractModel):
    """Selected shipping and logistics speed option (Section 7.41)."""
    id: str
    name: str
    description: str
    fee: float = Field(default=0.0, ge=0.0)
    estimated_time: str


class PaymentMethodContract(BaseContractModel):
    """Selected payment provider or card token (Section 7.41)."""
    id: str
    method_type: str = Field(..., description="card | upi | netbanking | cod")
    title: str
    last4: str | None = Field(default=None)
    is_selected: bool = Field(default=False)


class CheckoutStateContract(BaseContractModel):
    """Multi-step checkout session state (Section 7.41 - 7.44)."""
    checkout_id: str
    current_step: CheckoutStep = Field(default=CheckoutStep.CONTACT)
    cart: CartContract
    delivery_address: DeliveryAddressContract | None = Field(default=None)
    delivery_method: DeliveryMethodContract | None = Field(default=None)
    payment_method: PaymentMethodContract | None = Field(default=None)
    is_ready_to_place: bool = Field(default=False)


class OrderItemContract(BaseContractModel):
    """Line item in a placed order (Section 7.50)."""
    product_id: str
    title: str
    brand: str
    media_uri: str
    selected_variants: dict[str, str] = Field(default_factory=dict)
    quantity: int = Field(default=1, ge=1)
    unit_price: PriceSpecContract
    total_price: PriceSpecContract


class OrderContract(BaseContractModel):
    """Authoritative placed order detail (Section 7.48 - 7.50)."""
    order_id: str
    order_number: str
    placed_at: str
    status: OrderStatus = Field(default=OrderStatus.PLACED)
    items: list[OrderItemContract] = Field(default_factory=list)
    delivery_address: DeliveryAddressContract
    delivery_method: DeliveryMethodContract
    payment_summary: str
    price_summary: CartSummaryContract


# ---------------------------------------------------------------------------
# Interaction Request / Response Payloads (Sections 7.31, 7.35, 7.46)
# ---------------------------------------------------------------------------

class AddToCartRequestContract(BaseContractModel):
    """Payload to add a product variant to the cart (Section 7.31)."""
    product_id: str
    quantity: int = Field(default=1, ge=1, le=10)
    selected_variants: dict[str, str] = Field(default_factory=dict)


class UpdateCartQuantityRequestContract(BaseContractModel):
    """Payload to increment/decrement/remove cart quantity (Section 7.39)."""
    item_id: str
    quantity: int = Field(ge=0, le=10)


class WishlistToggleRequestContract(BaseContractModel):
    """Payload to add/remove a product from wishlist (Section 7.33)."""
    product_id: str
    currently_wishlisted: bool


class WishlistToggleResultContract(BaseContractModel):
    """Response returned when toggling wishlist state."""
    product_id: str
    is_in_wishlist: bool
    total_wishlist_count: int = Field(ge=0)
    message: str


class CheckoutSubmitRequestContract(BaseContractModel):
    """Payload to place final order (Section 7.46)."""
    checkout_id: str
    payment_method_id: str


# ---------------------------------------------------------------------------
# 12 Shopping Template Specifications (SH01 - SH12, Section 7.4 & 7.70)
# ---------------------------------------------------------------------------

class ShoppingHomeTemplateSpecContract(BaseContractModel):
    """SH01: Shopping Home combining discovery and commerce (Section 7.6)."""
    screen_id: ShoppingScreenId = Field(default=ShoppingScreenId.SH01_SHOPPING_HOME)
    search_placeholder: str = Field(default="Search luxury fashion, streetwear, shoes...")
    featured_collection_ids: list[str] = Field(default_factory=list)
    categories: list[dict[str, str]] = Field(default_factory=list)
    trending_product_ids: list[str] = Field(default_factory=list)
    recommended_product_ids: list[str] = Field(default_factory=list)


class CategoryTemplateSpecContract(BaseContractModel):
    """SH02: Category browsing screen with subcategory hierarchy (Section 7.7)."""
    screen_id: ShoppingScreenId = Field(default=ShoppingScreenId.SH02_CATEGORY)
    category_id: str
    category_name: str
    parent_category_name: str | None = Field(default=None)
    subcategories: list[dict[str, str]] = Field(default_factory=list)
    featured_product_ids: list[str] = Field(default_factory=list)


class SearchResultsTemplateSpecContract(BaseContractModel):
    """Search results with suggestions and spellcheck (Section 7.19 & 7.20)."""
    query: str
    total_results: int = Field(default=0, ge=0)
    suggestions: list[str] = Field(default_factory=list)
    filter_state: FilterStateContract
    product_ids: list[str] = Field(default_factory=list)


class ProductDetailTemplateSpecContract(BaseContractModel):
    """SH07-adjacent / Product Detail Screen Template (Section 7.21)."""
    product: ShoppingProductDetailContract
    breadcrumb_trail: list[str] = Field(default_factory=list)
    sticky_action_enabled: bool = Field(default=True)


class WishlistTemplateSpecContract(BaseContractModel):
    """SH05: Wishlist screen template (Section 7.33)."""
    screen_id: ShoppingScreenId = Field(default=ShoppingScreenId.SH05_WISHLIST)
    wishlist: WishlistContract
    sort_options: list[str] = Field(default_factory=list)


class CartTemplateSpecContract(BaseContractModel):
    """SH06: Shopping Cart template (Section 7.36)."""
    screen_id: ShoppingScreenId = Field(default=ShoppingScreenId.SH06_CART)
    cart: CartContract
    suggested_cross_sell_ids: list[str] = Field(default_factory=list)


class CheckoutTemplateSpecContract(BaseContractModel):
    """SH08: Progressive Checkout template (Section 7.41)."""
    screen_id: ShoppingScreenId = Field(default=ShoppingScreenId.SH08_CHECKOUT)
    checkout_state: CheckoutStateContract
    available_addresses: list[DeliveryAddressContract] = Field(default_factory=list)
    available_delivery_methods: list[DeliveryMethodContract] = Field(default_factory=list)
    available_payment_methods: list[PaymentMethodContract] = Field(default_factory=list)


class OrderReviewTemplateSpecContract(BaseContractModel):
    """SH09: Final pre-submission order review (Section 7.45)."""
    screen_id: ShoppingScreenId = Field(default=ShoppingScreenId.SH09_ORDER_REVIEW)
    checkout_id: str
    items: list[CartItemContract] = Field(default_factory=list)
    delivery_address: DeliveryAddressContract
    delivery_method: DeliveryMethodContract
    payment_method: PaymentMethodContract
    summary: CartSummaryContract


class ConfirmationTemplateSpecContract(BaseContractModel):
    """SH10: Order confirmation and next actions (Section 7.47)."""
    screen_id: ShoppingScreenId = Field(default=ShoppingScreenId.SH10_ORDER_CONFIRMATION)
    order_number: str
    order_id: str
    placed_at: str
    estimated_delivery: str
    items_count: int = Field(ge=1)
    total_amount: float = Field(ge=0.0)
    currency_symbol: str = Field(default="₹")


class OrdersTemplateSpecContract(BaseContractModel):
    """SH11: Customer order history list (Section 7.48)."""
    screen_id: ShoppingScreenId = Field(default=ShoppingScreenId.SH11_ORDERS)
    orders: list[OrderContract] = Field(default_factory=list)
    total_orders: int = Field(default=0, ge=0)


class OrderDetailTemplateSpecContract(BaseContractModel):
    """SH12: Granular order inspection and tracking (Section 7.50)."""
    screen_id: ShoppingScreenId = Field(default=ShoppingScreenId.SH12_ORDER_DETAIL)
    order: OrderContract
    tracking_steps: list[dict[str, str]] = Field(default_factory=list)
