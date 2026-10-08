from __future__ import annotations

from app.core.runtime import CoreRuntime, get_core_runtime
from fashx.domain.analytics.service import AnalyticsService
from fashx.domain.cart.service import CartService
from fashx.domain.checkout.service import CheckoutService
from fashx.domain.commerce.service import CommerceService
from fashx.domain.customer.service import CustomerService
from fashx.domain.fashion.service import FashionService
from fashx.domain.fulfillment.carrier import TestCarrierProvider
from fashx.domain.fulfillment.service import FulfillmentService
from fashx.domain.inventory.service import InventoryService
from fashx.domain.order.service import OrderService
from fashx.domain.payments.provider import TestPaymentProvider
from fashx.domain.payments.service import PaymentService
from fashx.domain.pricing.service import PricingService
from fashx.domain.promotions.service import PromotionService
from fashx.domain.recommendations.provider import DefaultPersonalizationProvider
from fashx.domain.recommendations.service import RecommendationService
from fashx.domain.returns.service import ReturnsService
from fashx.domain.trends.service import TrendService
from fashx.repositories.analytics.memory import (
    InMemoryAnalyticsEventRepository,
    InMemoryAnalyticsMetricRepository,
)
from fashx.repositories.cart.memory import (
    InMemoryCartLineRepository,
    InMemoryCartRepository,
)
from fashx.repositories.checkout.memory import InMemoryCheckoutRepository
from fashx.repositories.commerce.memory import (
    InMemoryBrandRepository,
    InMemoryListingRepository,
    InMemoryMarketplaceRepository,
    InMemoryProductBrandRepository,
    InMemorySellerRepository,
)
from fashx.repositories.customer.memory import (
    InMemoryCustomerAddressRepository,
    InMemoryCustomerConsentRepository,
    InMemoryCustomerPreferenceRepository,
    InMemoryCustomerPreferencesRepository,
    InMemoryCustomerRepository,
)
from fashx.repositories.fashion.memory import (
    InMemoryProductFashionRepository,
    InMemoryTaxonomyRepository,
)
from fashx.repositories.fulfillment.memory import (
    InMemoryFulfillmentLineRepository,
    InMemoryFulfillmentRepository,
    InMemoryShipmentPackageRepository,
    InMemoryShipmentRepository,
)
from fashx.repositories.inventory.memory import (
    InMemoryInventoryRepository,
    InMemoryStockLocationRepository,
    InMemoryStockMovementRepository,
)
from fashx.repositories.order.memory import (
    InMemoryOrderLineRepository,
    InMemoryOrderRepository,
)
from fashx.repositories.payments.memory import (
    InMemoryPaymentRepository,
    InMemoryPaymentTransactionRepository,
)
from fashx.repositories.pricing.memory import (
    InMemoryPriceRepository,
    InMemoryPricingRuleRepository,
)
from fashx.repositories.promotions.memory import (
    InMemoryOfferRepository,
    InMemoryPromotionRepository,
)
from fashx.repositories.recommendations.memory import (
    InMemoryRecommendationCandidateRepository,
)
from fashx.repositories.returns.memory import (
    InMemoryCancellationRepository,
    InMemoryRefundRepository,
    InMemoryReplacementRepository,
    InMemoryReturnLineRepository,
    InMemoryReturnRepository,
)
from fashx.repositories.trends.memory import (
    InMemoryTrendObservationRepository,
    InMemoryTrendRepository,
)


def register_core_services(runtime: CoreRuntime | None = None) -> CoreRuntime:
    if runtime is None:
        runtime = get_core_runtime()

    if not runtime.registry.contains("taxonomy_repository"):
        runtime.registry.register(
            "taxonomy_repository",
            InMemoryTaxonomyRepository(),
        )

    if not runtime.registry.contains("product_fashion_repository"):
        runtime.registry.register(
            "product_fashion_repository",
            InMemoryProductFashionRepository(),
        )

    if not runtime.registry.contains("fashion_service"):
        fashion_service = FashionService(
            taxonomy_repository=runtime.registry.get("taxonomy_repository"),
            classification_repository=runtime.registry.get(
                "product_fashion_repository"
            ),
            event_bus=runtime.event_bus,
        )

        runtime.registry.register(
            "fashion_service",
            fashion_service,
        )

    if not runtime.registry.contains("product_service"):
        runtime.registry.register(
            "product_service",
            runtime.registry.get("fashion_service"),
        )

    if not runtime.registry.contains("brand_repository"):
        runtime.registry.register(
            "brand_repository",
            InMemoryBrandRepository(),
        )

    if not runtime.registry.contains("seller_repository"):
        runtime.registry.register(
            "seller_repository",
            InMemorySellerRepository(),
        )

    if not runtime.registry.contains("marketplace_repository"):
        runtime.registry.register(
            "marketplace_repository",
            InMemoryMarketplaceRepository(),
        )

    if not runtime.registry.contains("product_brand_repository"):
        runtime.registry.register(
            "product_brand_repository",
            InMemoryProductBrandRepository(),
        )

    if not runtime.registry.contains("listing_repository"):
        runtime.registry.register(
            "listing_repository",
            InMemoryListingRepository(),
        )

    if not runtime.registry.contains("commerce_service"):
        commerce_service = CommerceService(
            brand_repository=runtime.registry.get("brand_repository"),
            seller_repository=runtime.registry.get("seller_repository"),
            marketplace_repository=runtime.registry.get("marketplace_repository"),
            product_brand_repository=runtime.registry.get("product_brand_repository"),
            listing_repository=runtime.registry.get("listing_repository"),
            event_bus=runtime.event_bus,
        )

        runtime.registry.register(
            "commerce_service",
            commerce_service,
        )

    if not runtime.registry.contains("inventory_repository"):
        runtime.registry.register(
            "inventory_repository",
            InMemoryInventoryRepository(),
        )

    if not runtime.registry.contains("stock_location_repository"):
        runtime.registry.register(
            "stock_location_repository",
            InMemoryStockLocationRepository(),
        )

    if not runtime.registry.contains("stock_movement_repository"):
        runtime.registry.register(
            "stock_movement_repository",
            InMemoryStockMovementRepository(),
        )

    if not runtime.registry.contains("inventory_service"):
        inventory_service = InventoryService(
            inventory_repository=runtime.registry.get(
                "inventory_repository"
            ),
            location_repository=runtime.registry.get(
                "stock_location_repository"
            ),
            movement_repository=runtime.registry.get(
                "stock_movement_repository"
            ),
            event_bus=runtime.event_bus,
        )

        runtime.registry.register(
            "inventory_service",
            inventory_service,
        )

    if not runtime.registry.contains("promotion_repository"):
        runtime.registry.register(
            "promotion_repository",
            InMemoryPromotionRepository(),
        )

    if not runtime.registry.contains("offer_repository"):
        runtime.registry.register(
            "offer_repository",
            InMemoryOfferRepository(),
        )

    if not runtime.registry.contains("promotion_service"):
        promotion_service = PromotionService(
            promotion_repository=runtime.registry.get(
                "promotion_repository"
            ),
            offer_repository=runtime.registry.get(
                "offer_repository"
            ),
            event_bus=runtime.event_bus,
        )

        runtime.registry.register(
            "promotion_service",
            promotion_service,
        )

    if not runtime.registry.contains("cart_repository"):
        runtime.registry.register(
            "cart_repository",
            InMemoryCartRepository(),
        )

    if not runtime.registry.contains("cart_line_repository"):
        runtime.registry.register(
            "cart_line_repository",
            InMemoryCartLineRepository(),
        )

    if not runtime.registry.contains("cart_service"):
        cart_service = CartService(
            cart_repository=runtime.registry.get("cart_repository"),
            line_repository=runtime.registry.get("cart_line_repository"),
            event_bus=runtime.event_bus,
        )

        runtime.registry.register(
            "cart_service",
            cart_service,
        )

    if not runtime.registry.contains("order_repository"):
        runtime.registry.register(
            "order_repository",
            InMemoryOrderRepository(),
        )

    if not runtime.registry.contains("order_line_repository"):
        runtime.registry.register(
            "order_line_repository",
            InMemoryOrderLineRepository(),
        )

    if not runtime.registry.contains("checkout_repository"):
        runtime.registry.register(
            "checkout_repository",
            InMemoryCheckoutRepository(),
        )

    if not runtime.registry.contains("order_service"):
        order_service = OrderService(
            order_repository=runtime.registry.get("order_repository"),
            line_repository=runtime.registry.get("order_line_repository"),
            event_bus=runtime.event_bus,
        )
        runtime.registry.register(
            "order_service",
            order_service,
        )

    if not runtime.registry.contains("checkout_service"):
        checkout_service = CheckoutService(
            checkout_repository=runtime.registry.get(
                "checkout_repository"
            ),
            event_bus=runtime.event_bus,
            order_service=runtime.registry.get("order_service"),
            cart_repository=(
                runtime.registry.get("cart_repository")
                if runtime.registry.contains("cart_repository")
                else None
            ),
            cart_line_repository=(
                runtime.registry.get("cart_line_repository")
                if runtime.registry.contains("cart_line_repository")
                else None
            ),
        )

        runtime.registry.register(
            "checkout_service",
            checkout_service,
        )

    if not runtime.registry.contains("payment_repository"):
        runtime.registry.register(
            "payment_repository",
            InMemoryPaymentRepository(),
        )

    if not runtime.registry.contains("payment_transaction_repository"):
        runtime.registry.register(
            "payment_transaction_repository",
            InMemoryPaymentTransactionRepository(),
        )

    if not runtime.registry.contains("payment_service"):
        payment_service = PaymentService(
            payment_repository=runtime.registry.get(
                "payment_repository"
            ),
            transaction_repository=runtime.registry.get(
                "payment_transaction_repository"
            ),
            event_bus=runtime.event_bus,
            provider=TestPaymentProvider(),
        )

        runtime.registry.register(
            "payment_service",
            payment_service,
        )

    if not runtime.registry.contains("fulfillment_repository"):
        runtime.registry.register(
            "fulfillment_repository",
            InMemoryFulfillmentRepository(),
        )

    if not runtime.registry.contains("fulfillment_line_repository"):
        runtime.registry.register(
            "fulfillment_line_repository",
            InMemoryFulfillmentLineRepository(),
        )

    if not runtime.registry.contains("shipment_repository"):
        runtime.registry.register(
            "shipment_repository",
            InMemoryShipmentRepository(),
        )

    if not runtime.registry.contains("shipment_package_repository"):
        runtime.registry.register(
            "shipment_package_repository",
            InMemoryShipmentPackageRepository(),
        )

    if not runtime.registry.contains("fulfillment_service"):
        fulfillment_service = FulfillmentService(
            fulfillment_repository=runtime.registry.get(
                "fulfillment_repository"
            ),
            line_repository=runtime.registry.get(
                "fulfillment_line_repository"
            ),
            shipment_repository=runtime.registry.get(
                "shipment_repository"
            ),
            event_bus=runtime.event_bus,
            carrier=TestCarrierProvider(),
        )

        runtime.registry.register(
            "fulfillment_service",
            fulfillment_service,
        )

    if not runtime.registry.contains("customer_repository"):
        runtime.registry.register(
            "customer_repository",
            InMemoryCustomerRepository(),
        )

    if not runtime.registry.contains("customer_address_repository"):
        runtime.registry.register(
            "customer_address_repository",
            InMemoryCustomerAddressRepository(),
        )

    if not runtime.registry.contains("customer_preference_repository"):
        runtime.registry.register(
            "customer_preference_repository",
            InMemoryCustomerPreferenceRepository(),
        )

    if not runtime.registry.contains("customer_preferences_repository"):
        runtime.registry.register(
            "customer_preferences_repository",
            InMemoryCustomerPreferencesRepository(),
        )

    if not runtime.registry.contains("customer_consent_repository"):
        runtime.registry.register(
            "customer_consent_repository",
            InMemoryCustomerConsentRepository(),
        )

    if not runtime.registry.contains("customer_service"):
        customer_service = CustomerService(
            customer_repository=runtime.registry.get(
                "customer_repository"
            ),
            address_repository=runtime.registry.get(
                "customer_address_repository"
            ),
            preferences_repository=runtime.registry.get(
                "customer_preferences_repository"
            ),
            consent_repository=runtime.registry.get(
                "customer_consent_repository"
            ),
            preference_repository=runtime.registry.get(
                "customer_preference_repository"
            ),
            event_bus=runtime.event_bus,
        )

        runtime.registry.register(
            "customer_service",
            customer_service,
        )


    if not runtime.registry.contains("return_repository"):
        runtime.registry.register(
            "return_repository",
            InMemoryReturnRepository(),
        )

    if not runtime.registry.contains("return_line_repository"):
        runtime.registry.register(
            "return_line_repository",
            InMemoryReturnLineRepository(),
        )

    if not runtime.registry.contains("cancellation_repository"):
        runtime.registry.register(
            "cancellation_repository",
            InMemoryCancellationRepository(),
        )

    if not runtime.registry.contains("refund_repository"):
        runtime.registry.register(
            "refund_repository",
            InMemoryRefundRepository(),
        )

    if not runtime.registry.contains("replacement_repository"):
        runtime.registry.register(
            "replacement_repository",
            InMemoryReplacementRepository(),
        )

    if not runtime.registry.contains("returns_service"):
        returns_service = ReturnsService(
            return_repository=runtime.registry.get(
                "return_repository"
            ),
            return_line_repository=runtime.registry.get(
                "return_line_repository"
            ),
            cancellation_repository=runtime.registry.get(
                "cancellation_repository"
            ),
            refund_repository=runtime.registry.get(
                "refund_repository"
            ),
            replacement_repository=runtime.registry.get(
                "replacement_repository"
            ),
            event_bus=runtime.event_bus,
        )

        runtime.registry.register(
            "returns_service",
            returns_service,
        )

    if not runtime.registry.contains("price_repository"):
        runtime.registry.register(
            "price_repository",
            InMemoryPriceRepository(),
        )

    if not runtime.registry.contains("pricing_rule_repository"):
        runtime.registry.register(
            "pricing_rule_repository",
            InMemoryPricingRuleRepository(),
        )

    if not runtime.registry.contains("pricing_service"):
        pricing_service = PricingService(
            price_repository=runtime.registry.get(
                "price_repository"
            ),
            rule_repository=runtime.registry.get(
                "pricing_rule_repository"
            ),
            event_bus=runtime.event_bus,
        )

        runtime.registry.register(
            "pricing_service",
            pricing_service,
        )

    if not runtime.registry.contains("recommendation_candidate_repository"):
        runtime.registry.register(
            "recommendation_candidate_repository",
            InMemoryRecommendationCandidateRepository(),
        )

    if not runtime.registry.contains("personalization_provider"):
        runtime.registry.register(
            "personalization_provider",
            DefaultPersonalizationProvider(),
        )

    if not runtime.registry.contains("recommendation_service"):
        recommendation_service = RecommendationService(
            candidate_repository=runtime.registry.get(
                "recommendation_candidate_repository"
            ),
            personalization_provider=runtime.registry.get(
                "personalization_provider"
            ),
            event_bus=runtime.event_bus,
        )

        runtime.registry.register(
            "recommendation_service",
            recommendation_service,
        )

    if not runtime.registry.contains("trend_repository"):
        runtime.registry.register(
            "trend_repository",
            InMemoryTrendRepository(),
        )

    if not runtime.registry.contains("trend_observation_repository"):
        runtime.registry.register(
            "trend_observation_repository",
            InMemoryTrendObservationRepository(),
        )

    if not runtime.registry.contains("trend_service"):
        trend_service = TrendService(
            trend_repository=runtime.registry.get(
                "trend_repository"
            ),
            observation_repository=runtime.registry.get(
                "trend_observation_repository"
            ),
            event_bus=runtime.event_bus,
        )

        runtime.registry.register(
            "trend_service",
            trend_service,
        )

    if not runtime.registry.contains("analytics_event_repository"):
        runtime.registry.register(
            "analytics_event_repository",
            InMemoryAnalyticsEventRepository(),
        )

    if not runtime.registry.contains("analytics_metric_repository"):
        runtime.registry.register(
            "analytics_metric_repository",
            InMemoryAnalyticsMetricRepository(),
        )

    if not runtime.registry.contains("analytics_service"):
        analytics_service = AnalyticsService(
            event_repository=runtime.registry.get(
                "analytics_event_repository"
            ),
            metric_repository=runtime.registry.get(
                "analytics_metric_repository"
            ),
            event_bus=runtime.event_bus,
        )

        runtime.registry.register(
            "analytics_service",
            analytics_service,
        )

    return runtime


REQUIRED_COMPONENTS: list[str] = [
    "fashion_service",
    "commerce_service",
    "inventory_service",
    "promotion_service",
    "cart_service",
    "order_service",
    "checkout_service",
    "payment_service",
    "fulfillment_service",
    "customer_service",
    "returns_service",
    "pricing_service",
    "recommendation_service",
    "trend_service",
    "analytics_service",
]


def validate_runtime(
    runtime: CoreRuntime | None = None,
    required_components: list[str] | None = None,
) -> bool:
    if runtime is None:
        runtime = get_core_runtime()
    components = (
        required_components if required_components is not None else REQUIRED_COMPONENTS
    )
    missing = [c for c in components if not runtime.registry.contains(c)]
    if missing:
        raise RuntimeError(f"Runtime validation failed. Missing components: {missing}")
    return True


validate_required_services = validate_runtime

