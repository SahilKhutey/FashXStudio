from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth.dependencies import current_user_id
from api.app.catalog.repositories.catalog import CatalogRepository
from api.app.core.dependencies import db_session
from api.app.wardrobe.application import WardrobeDecisionService
from api.app.wardrobe.repository import WardrobeRepository
from schemas.catalog.detail import RejectCatalogItemResponse, SaveCatalogItemRequest, SaveCatalogItemResponse

router = APIRouter(prefix="/api/v1/wardrobe", tags=["wardrobe"])


def get_service(session: AsyncSession = Depends(db_session)) -> WardrobeDecisionService:
    return WardrobeDecisionService(WardrobeRepository(session), CatalogRepository(session))


@router.post("/save/{product_id}", response_model=SaveCatalogItemResponse)
async def save_product(
    product_id: UUID,
    payload: SaveCatalogItemRequest,
    user_id: UUID = Depends(current_user_id),
    service: WardrobeDecisionService = Depends(get_service),
) -> SaveCatalogItemResponse:
    return await service.save(user_id, product_id, payload)


@router.post("/reject/{product_id}", response_model=RejectCatalogItemResponse)
async def reject_product(
    product_id: UUID,
    user_id: UUID = Depends(current_user_id),
    service: WardrobeDecisionService = Depends(get_service),
) -> RejectCatalogItemResponse:
    return await service.reject(user_id, product_id)
