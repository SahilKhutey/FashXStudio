from .analytics import router as analytics_router
from .analytics_schemas import (
    AnalyticsAggregateRequest,
    AnalyticsEventRequest,
)
from .cart import router as cart_router
from .cart_schemas import (
    CartCreateRequest,
    CartLineCreateRequest,
    CartLineResponse,
    CartResponse,
    CartTotalsResponse,
    QuantityUpdateRequest,
)
from .checkout import router as checkout_router
from .checkout_schemas import (
    CheckoutCreateRequest,
    CheckoutResponse,
)
from .commerce import router as commerce_router
from .commerce_schemas import (
    BrandCreateRequest,
    BrandResponse,
    ListingCreateRequest,
    ListingResponse,
    ListingStatusRequest,
    MarketplaceCreateRequest,
    MarketplaceResponse,
    ProductBrandRequest,
    ProductBrandResponse,
    SellerCreateRequest,
    SellerResponse,
)
from .customer import router as customer_router
from .customer_schemas import (
    AddressCreateRequest,
    AddressResponse,
    ConsentCreateRequest,
    ConsentResponse,
    CustomerCreateRequest,
    CustomerResponse,
    CustomerUpdateRequest,
    PreferenceRequest,
    PreferenceResponse,
    PreferencesRequest,
    PreferencesResponse,
)
from .fashion import router as fashion_router
from .fashion_schemas import (
    FashionAttributeRequest,
    FashionClassificationResponse,
    ProductFashionClassificationRequest,
    TaxonomyCreateRequest,
    TaxonomyResponse,
)
from .fulfillment import router as fulfillment_router
from .fulfillment_schemas import (
    AddressRequest,
    FulfillmentCreateRequest,
    FulfillmentLineRequest,
    FulfillmentResponse,
    ShipmentCreateRequest,
    ShipmentResponse,
)
from .inventory import router as inventory_router
from .inventory_schemas import (
    InventoryCreateRequest,
    InventoryResponse,
    InventoryStatusRequest,
    StockAdjustmentRequest,
    StockLocationCreateRequest,
    StockLocationResponse,
)
from .order_schemas import (
    OrderResponse,
)
from .orders import router as orders_router
from .payment_schemas import (
    PaymentAuthorizeRequest,
    PaymentCreateRequest,
    PaymentResponse,
)
from .payments import router as payments_router
from .pricing import router as pricing_router
from .pricing_schemas import (
    PriceAdjustmentResponse,
    PriceCalculateRequest,
    PriceCalculationResponse,
    PriceCreateRequest,
    RuleCreateRequest,
)
from .promotion_schemas import (
    CalculateOfferRequest,
    OfferCalculationResponse,
    OfferCreateRequest,
    OfferResponse,
    OfferStatusRequest,
    PromotionCreateRequest,
    PromotionResponse,
    PromotionStatusRequest,
)
from .promotions import router as promotions_router
from .recommendation_schemas import (
    RecommendationExplanationResponse,
    RecommendationItemResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from .recommendations import router as recommendations_router
from .returns import router as returns_router
from .returns_schemas import (
    CancellationCreateRequest,
    CancellationResponse,
    RefundCreateRequest,
    RefundResponse,
    ReturnCreateRequest,
    ReturnLineRequest,
    ReturnResponse,
)
from .system import router as system_router
from .trend_schemas import (
    TrendCreateRequest,
    TrendObservationRequest,
)
from .trends import router as trends_router

customers_router = customer_router

__all__ = [
    "AddressCreateRequest",
    "AddressRequest",
    "AddressResponse",
    "AnalyticsAggregateRequest",
    "AnalyticsEventRequest",
    "BrandCreateRequest",
    "BrandResponse",
    "CalculateOfferRequest",
    "CancellationCreateRequest",
    "CancellationResponse",
    "CartCreateRequest",
    "CartLineCreateRequest",
    "CartLineResponse",
    "CartResponse",
    "CartTotalsResponse",
    "CheckoutCreateRequest",
    "CheckoutLineRequest",
    "CheckoutResponse",
    "CompleteCheckoutRequest",
    "ConsentCreateRequest",
    "ConsentResponse",
    "CustomerCreateRequest",
    "CustomerResponse",
    "CustomerUpdateRequest",

    "FashionAttributeRequest",
    "FashionClassificationResponse",
    "FulfillmentCreateRequest",
    "FulfillmentLineRequest",
    "FulfillmentResponse",
    "InventoryCreateRequest",
    "InventoryResponse",
    "InventoryStatusRequest",
    "ListingCreateRequest",
    "ListingResponse",
    "ListingStatusRequest",
    "MarketplaceCreateRequest",
    "MarketplaceResponse",
    "OfferCalculationResponse",
    "OfferCreateRequest",
    "OfferResponse",
    "OfferStatusRequest",
    "OrderResponse",
    "PaymentAuthorizeRequest",
    "PaymentCreateRequest",
    "PaymentResponse",
    "PreferenceRequest",

    "PreferenceResponse",
    "PreferencesRequest",
    "PreferencesResponse",
    "PriceAdjustmentResponse",
    "PriceCalculateRequest",
    "PriceCalculationResponse",
    "PriceCreateRequest",
    "ProductBrandRequest",
    "ProductBrandResponse",
    "ProductFashionClassificationRequest",
    "PromotionCreateRequest",
    "PromotionResponse",
    "PromotionStatusRequest",
    "QuantityUpdateRequest",
    "RecommendationExplanationResponse",
    "RecommendationItemResponse",
    "RecommendationRequest",
    "RecommendationResponse",
    "RefundCreateRequest",
    "RefundResponse",
    "ReturnCreateRequest",
    "ReturnLineRequest",
    "ReturnResponse",
    "RuleCreateRequest",
    "SellerCreateRequest",
    "SellerResponse",
    "ShipmentCreateRequest",
    "ShipmentResponse",
    "StockAdjustmentRequest",
    "StockLocationCreateRequest",
    "StockLocationResponse",
    "TaxonomyCreateRequest",
    "TaxonomyResponse",
    "TrendCreateRequest",
    "TrendObservationRequest",
    "analytics_router",
    "cart_router",
    "checkout_router",
    "commerce_router",
    "customer_router",
    "customers_router",
    "fashion_router",
    "fulfillment_router",
    "inventory_router",
    "orders_router",
    "payments_router",
    "pricing_router",
    "promotions_router",
    "recommendations_router",
    "returns_router",
    "system_router",
    "trends_router",
]


