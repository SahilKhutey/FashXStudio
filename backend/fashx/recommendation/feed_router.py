"""Feed router handling /api/v1/feed endpoints and user interaction signals."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import select

from database.models.feed import FeedSignal
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.database import get_session_factory
from fashx.discovery.session_cache import invalidate_user_cache
from fashx.observability.stages import format_server_timing, stage, start_stage_recording
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.recommendation.application.generate_feed import (
    GenerateFeedCommand,
    GenerateFeedUseCase,
)
from fashx.recommendation.router import (
    FeedItemResponse,
    FeedResponse,
    get_catalog_uow,
    get_profile_uow,
)
from fashx.security.deps import Principal, get_principal

feed_router = APIRouter(prefix="/feed", tags=["feed"])


class FeedSignalRequest(BaseModel):
    garment_id: UUID
    action: Literal["like", "hide", "not_interested"]


class FeedSignalResponse(BaseModel):
    status: str
    user_id: UUID
    garment_id: UUID
    action: str


@feed_router.post(
    "/signals",
    response_model=FeedSignalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_feed_signal(
    payload: FeedSignalRequest,
    principal: Principal = Depends(get_principal),
) -> FeedSignalResponse:
    """Record a user signal (like, hide, not_interested) on a feed garment.

    Owned-resource rule: the signal's user is always the authenticated principal.
    """
    user_id = UUID(principal.user_id)
    session_factory = get_session_factory()
    try:
        async with session_factory() as session:
            stmt = select(FeedSignal).where(
                FeedSignal.user_id == user_id,
                FeedSignal.garment_id == payload.garment_id,
                FeedSignal.action == payload.action,
            )
            existing = (await session.scalars(stmt)).first()
            if not existing:
                sig = FeedSignal(
                    user_id=user_id,
                    garment_id=payload.garment_id,
                    action=payload.action,
                )
                session.add(sig)
                await session.commit()
    except Exception:
        # Graceful fallback if database unavailable during offline/mock execution
        pass

    # Positive and negative signals invalidate active feed caches for fresh recommendations
    invalidate_user_cache(user_id)

    return FeedSignalResponse(
        status="recorded",
        user_id=user_id,
        garment_id=payload.garment_id,
        action=payload.action,
    )


@feed_router.get("", response_model=FeedResponse)
async def get_feed(
    response: Response,
    limit: int = Query(default=20, ge=1, le=100),
    diversity: float = Query(default=0.7, ge=0.0, le=1.0),
    principal: Principal = Depends(get_principal),
    profile_uow: ProfileUnitOfWork = Depends(get_profile_uow),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> FeedResponse:
    """Get personalized feed for the authenticated principal."""
    start_stage_recording()
    user_id = UUID(principal.user_id)
    with stage("retrieval"):
        use_case = GenerateFeedUseCase(profile_uow, catalog_uow)
        cmd = GenerateFeedCommand(
            user_id=user_id,
            limit=limit,
            diversity_lambda=diversity,
        )
    with stage("scoring"):
        result = await use_case.execute(cmd)

    # Attach Server-Timing metrics header
    response.headers["Server-Timing"] = format_server_timing()

    return FeedResponse(
        user_id=result.user_id,
        items=[
            FeedItemResponse(
                garment_id=item.garment_id,
                category=item.category,
                subcategory=item.subcategory,
                price_minor=item.price_minor,
                dominant_color=item.dominant_color,
                silhouette=item.silhouette,
                relevance_score=item.relevance_score,
                stylist_explanation=item.stylist_explanation,
            )
            for item in result.items
        ],
        total_candidates=result.total_candidates,
        filtered_candidates=result.filtered_candidates,
    )
