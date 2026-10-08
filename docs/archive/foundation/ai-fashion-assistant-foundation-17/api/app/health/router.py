from datetime import datetime, timezone

from fastapi import APIRouter

from schemas.common.health import HealthResponse

from ..core.database import check_database
from ..core.settings import get_settings

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/health/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc),
        database="not_checked",
    )


@router.get("/health/ready", response_model=HealthResponse)
async def readiness() -> HealthResponse:
    settings = get_settings()
    database_ok = await check_database()
    if settings.readiness_requires_database and not database_ok:
        return HealthResponse(
            status="degraded",
            service=settings.app_name,
            version=settings.app_version,
            timestamp=datetime.now(timezone.utc),
            database="error",
        )
    return HealthResponse(
        status="ok" if database_ok else "degraded",
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc),
        database="ok" if database_ok else "error",
    )
