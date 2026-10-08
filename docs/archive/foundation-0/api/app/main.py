from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .catalog.router import router as catalog_router
from .commerce_wardrobe.router import router as commerce_wardrobe_router
from .core.logging import configure_logging
from .core.observability import ContextFilter, configure_sentry
from .core.settings import get_settings
from .gateway.errors import install_exception_handlers
from .gateway.middleware import RequestContextMiddleware
from .health.router import router as health_router
from .profile.router import router as profile_router
from .recommendation.router import router as recommendation_router
from .tryon.router import router as tryon_router


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
    app.include_router(profile_router, prefix="/api/v1")
    app.include_router(catalog_router, prefix="/api/v1")
    app.include_router(recommendation_router, prefix="/api/v1")
    app.include_router(tryon_router, prefix="/api/v1")
    app.include_router(commerce_wardrobe_router, prefix="/api/v1")

    @app.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {"service": settings.app_name, "version": settings.app_version, "status": "ok"}

    return app


app = create_app()
