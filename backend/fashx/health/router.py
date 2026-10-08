from datetime import UTC, datetime

from fastapi import APIRouter
from schemas.common.health import HealthResponse

from api.app.core.database import check_database
from api.app.core.settings import get_settings

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/health/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(UTC),
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
            timestamp=datetime.now(UTC),
            database="error",
        )
    return HealthResponse(
        status="ok" if database_ok else "degraded",
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(UTC),
        database="ok" if database_ok else "error",
    )
