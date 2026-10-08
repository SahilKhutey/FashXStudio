from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.context import CoreContext
from app.core.runtime import get_core_runtime
from fashx.domain.trends.entities import (
    Trend,
    TrendObservation,
)
from fashx.domain.trends.enums import (
    SignalType,
    TrendSource,
    TrendType,
)
from fashx.domain.trends.service import TrendService

from .trend_schemas import (
    TrendCreateRequest,
    TrendObservationRequest,
)

router = APIRouter(
    prefix="/trends",
    tags=["trends"],
)


def get_trend_service() -> TrendService:
    return get_core_runtime().registry.get(
        "trend_service"
    )


@router.post("/observations")
async def create_observation(
    payload: TrendObservationRequest,
    service: TrendService = Depends(get_trend_service),
):
    observation = TrendObservation(
        topic=payload.topic,
        trend_type=payload.trend_type,
        signal_type=SignalType(payload.signal_type),
        source=TrendSource(payload.source),
        value=payload.value,
        region=payload.region,
    )

    return await service.create_observation(
        context=CoreContext.create(),
        observation=observation,
    )


@router.post("")
async def create_trend(
    payload: TrendCreateRequest,
    service: TrendService = Depends(get_trend_service),
):
    trend = Trend(
        topic=payload.topic,
        trend_type=TrendType(payload.trend_type),
        region=payload.region,
        strength=payload.strength,
        momentum=payload.momentum,
        confidence=payload.confidence,
    )

    return await service.create_trend(
        context=CoreContext.create(),
        trend=trend,
    )


@router.get("")
async def list_trends(
    region: str | None = None,
    trend_type: str | None = None,
    service: TrendService = Depends(get_trend_service),
):
    return await service.list_trends(
        region=region,
        trend_type=trend_type,
    )


@router.get("/{trend_id}")
async def get_trend(
    trend_id: UUID,
    service: TrendService = Depends(get_trend_service),
):
    return await service.get_trend(trend_id)


@router.post("/{trend_id}/activate")
async def activate_trend(
    trend_id: UUID,
    service: TrendService = Depends(get_trend_service),
):
    return await service.activate_trend(
        trend_id,
        context=CoreContext.create(),
    )
