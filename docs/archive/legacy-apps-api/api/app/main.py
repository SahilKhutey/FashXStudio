"""
FastAPI Modular Monolith Entrypoint (FashXStudio)
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.router import api_v1_router
from app.config.base import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation: verify configuration invariants
    settings = get_settings()
    # Lifespan yield
    yield
    # Graceful shutdown cleanup


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="FashXStudio API",
        description="AI Personal Fashion Operating System — Modular Monolith API",
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else ["https://fashx.studio"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # RFC 7807 Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "type": "https://api.fashx.studio/errors/internal-server-error",
                "title": "Internal Server Error",
                "status": 500,
                "detail": str(exc) if settings.DEBUG else "An unexpected error occurred.",
                "instance": str(request.url.path),
                "error_code": "ERR_INTERNAL_SERVER",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    # Mount API v1
    app.include_router(api_v1_router)

    return app


app = create_app()
