from fastapi import APIRouter

from fashx.core.health import core_health
from fashx.core.version import (
    CORE_API_VERSION,
    CORE_VERSION,
    PRODUCT_NAME,
)

router = APIRouter(
    prefix="/system",
    tags=["system"],
)


@router.get("/health")
async def health():
    report = core_health()
    return {
        "status": report.status,
        "product": PRODUCT_NAME,
        "core_version": CORE_VERSION,
        "api_version": CORE_API_VERSION,
        "details": report.details,
    }


@router.get("/ready")
async def ready():
    return {
        "status": "ready",
    }
