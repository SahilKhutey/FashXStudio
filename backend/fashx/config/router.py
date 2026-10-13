"""Remote config endpoint for client apps."""
from fastapi import APIRouter

from fashx.core.settings import get_settings

router = APIRouter(tags=["Config"])


@router.get("/config")
def config() -> dict:
    s = get_settings()
    return {
        "min_app_version": s.min_app_version,
        "maintenance": s.maintenance_mode,
        "tryon_supported_categories": s.tryon_supported_categories,
        "flags": {
            "tryon": s.tryon_enabled,
        },
    }
