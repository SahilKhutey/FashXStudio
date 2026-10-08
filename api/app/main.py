from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .catalog.router import router as catalog_router
from .commerce_wardrobe.router import router as commerce_wardrobe_router
from .core.logging import configure_logging
from .core.observability import ContextFilter, configure_sentry
from .core.settings import get_settings
from .features.router import router as features_router
from .gateway.errors import install_exception_handlers
from .gateway.middleware import RequestContextMiddleware
from .health.router import router as health_router
from .profile.router import router as profile_router
from .recommendation.router import router as recommendation_router
from .tryon.router import router as tryon_router
from .visual.router import router as visual_router


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    configure_sentry()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    from app.core.runtime import get_core_runtime

    runtime = get_core_runtime()
    app.state.core_runtime = runtime

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Idempotency-Key",
            "X-Request-ID",
            "X-Trace-ID",
        ],
    )

    import logging

    for handler in logging.getLogger().handlers:
        handler.addFilter(ContextFilter())

    install_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(features_router, prefix="/api/v1")
    app.include_router(profile_router, prefix="/api/v1")
    app.include_router(catalog_router, prefix="/api/v1")
    app.include_router(recommendation_router, prefix="/api/v1")
    app.include_router(tryon_router, prefix="/api/v1")
    app.include_router(commerce_wardrobe_router, prefix="/api/v1")
    app.include_router(visual_router, prefix="/api/v1")

    from app.api.v1.analytics import router as analytics_router
    from app.api.v1.cart import router as cart_router
    from app.api.v1.checkout import router as checkout_router
    from app.api.v1.commerce import router as commerce_router
    from app.api.v1.customer import router as customer_router
    from app.api.v1.fashion import router as fashion_router
    from app.api.v1.fulfillment import router as fulfillment_router
    from app.api.v1.inventory import router as inventory_router
    from app.api.v1.orders import router as orders_router
    from app.api.v1.payments import router as payments_router
    from app.api.v1.pricing import router as pricing_router
    from app.api.v1.promotions import router as promotions_router
    from app.api.v1.recommendations import router as recommendations_router
    from app.api.v1.returns import router as returns_router
    from app.api.v1.system import router as system_router
    from app.api.v1.trends import router as trends_router
    from app.core.bootstrap import register_core_services
    from app.core.errors import CoreError
    from fashx.integration.errors import core_error_handler

    app.add_exception_handler(CoreError, core_error_handler)
    register_core_services(runtime)
    app.include_router(fashion_router, prefix="/api/v1")
    app.include_router(commerce_router, prefix="/api/v1")
    app.include_router(inventory_router, prefix="/api/v1")
    app.include_router(promotions_router, prefix="/api/v1")
    app.include_router(cart_router, prefix="/api/v1")
    app.include_router(checkout_router, prefix="/api/v1")
    app.include_router(orders_router, prefix="/api/v1")
    app.include_router(payments_router, prefix="/api/v1")
    app.include_router(fulfillment_router, prefix="/api/v1")
    app.include_router(customer_router, prefix="/api/v1")
    app.include_router(returns_router, prefix="/api/v1")
    app.include_router(pricing_router, prefix="/api/v1")
    app.include_router(recommendations_router, prefix="/api/v1")
    app.include_router(trends_router, prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")
    app.include_router(system_router, prefix="/api/v1")


    @app.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {"service": settings.app_name, "version": settings.app_version, "status": "ok"}

    return app


app = create_app()
