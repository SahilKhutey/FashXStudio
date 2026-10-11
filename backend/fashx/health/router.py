from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from schemas.common.health import HealthResponse

from fashx.core.database import check_database
from fashx.core.settings import get_settings

router = APIRouter(prefix="/api/v1/system", tags=["system"])
healthz_router = APIRouter(tags=["system"])


async def check_redis_dependency(redis_url: str) -> bool:
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(redis_url, socket_timeout=1.5)
        pong = await client.ping()
        await client.aclose()
        return bool(pong)
    except Exception:
        return False


async def check_jwks_dependency(auth_mode: str, auth_jwks_url: str | None) -> bool:
    if auth_mode != "jwks":
        return True
    if not auth_jwks_url:
        return False
    try:
        import jwt

        client = jwt.PyJWKClient(auth_jwks_url, cache_keys=True)
        keys = client.get_signing_keys()
        return len(keys) > 0
    except Exception:
        return False


async def evaluate_readiness() -> tuple[bool, dict[str, str]]:
    settings = get_settings()
    deps: dict[str, str] = {}

    # 1. Postgres
    db_ok = await check_database()
    deps["postgres"] = "ok" if db_ok else "degraded"

    # 2. Redis
    redis_ok = await check_redis_dependency(settings.redis_url)
    deps["redis"] = "ok" if redis_ok else "degraded"

    # 3. JWKS
    jwks_ok = await check_jwks_dependency(settings.auth_mode, settings.auth_jwks_url)
    deps["jwks"] = "ok" if jwks_ok else "degraded"

    # Overall healthy
    if settings.is_production:
        all_ok = db_ok and redis_ok and jwks_ok
    else:
        # In non-production, database determines readiness unless redis is explicitly required
        all_ok = db_ok if settings.readiness_requires_database else True

    return all_ok, deps


@router.get("/health/live", response_model=HealthResponse)
@healthz_router.get("/healthz/live")
async def liveness() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(UTC),
        database="not_checked",
    )


@router.get("/health/ready")
@healthz_router.get("/healthz/ready")
async def readiness() -> Any:
    settings = get_settings()
    all_ok, deps = await evaluate_readiness()

    db_status = "ok" if deps.get("postgres") == "ok" else "error"
    overall_status = "ok" if all_ok else "degraded"

    body = {
        "status": overall_status,
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now(UTC).isoformat(),
        "database": db_status,
        "dependencies": deps,
    }

    if not all_ok:
        return JSONResponse(status_code=503, content=body)

    return JSONResponse(status_code=200, content=body)
