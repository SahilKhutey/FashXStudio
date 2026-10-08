from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth.dependencies import current_user_id
from api.app.catalog.repositories.catalog import CatalogRepository
from api.app.commerce.application import CommerceService
from api.app.commerce.integrations.configured_affiliate import ConfiguredAffiliateProvider
from api.app.commerce.repository import CommerceRepository
from api.app.core.dependencies import db_session
from api.app.core.settings import get_settings
from schemas.commerce.buy_click import BuyClickCreate, BuyClickResponse

router = APIRouter(prefix="/api/v1/commerce", tags=["commerce"])


def get_service(session: AsyncSession = Depends(db_session)) -> CommerceService:
    settings = get_settings()
    return CommerceService(
        commerce=CommerceRepository(session),
        catalog=CatalogRepository(session),
        affiliate=ConfiguredAffiliateProvider(settings),
    )


@router.post("/buy-click", response_model=BuyClickResponse, status_code=200)
async def create_buy_click(
    request: Request,
    payload: BuyClickCreate,
    user_id: UUID = Depends(current_user_id),
    service: CommerceService = Depends(get_service),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> BuyClickResponse:
    trace_id = getattr(request.state, "trace_id", None)
    return await service.create_buy_click(
        user_id=user_id,
        request=payload,
        trace_id=trace_id,
        idempotency_key=idempotency_key,
    )
