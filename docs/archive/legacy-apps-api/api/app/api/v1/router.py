"""
Aggregated API v1 Router
"""

from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.tryon import router as tryon_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router)
api_v1_router.include_router(tryon_router)
