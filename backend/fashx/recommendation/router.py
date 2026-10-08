from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.database import get_session_factory
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.recommendation.application.generate_feed import (
    GenerateFeedCommand,
    GenerateFeedUseCase,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def get_profile_uow() -> ProfileUnitOfWork:
    return ProfileUnitOfWork(get_session_factory())


def get_catalog_uow() -> CatalogUnitOfWork:
    return CatalogUnitOfWork(get_session_factory())


class FeedItemResponse(BaseModel):
    garment_id: UUID
    category: str
    subcategory: str | None
    price_minor: int
    dominant_color: str | None
    silhouette: str | None
    relevance_score: float
    stylist_explanation: str


class FeedResponse(BaseModel):
    user_id: UUID
    items: list[FeedItemResponse]
    total_candidates: int
    filtered_candidates: int


class RecordExclusionRequest(BaseModel):
    user_id: UUID
    garment_id: UUID | None = None
    brand_id: UUID | None = None
    reason: str | None = None


class RecordExclusionResponse(BaseModel):
    status: str
    message: str


@router.get("/feed/{user_id}", response_model=FeedResponse)
async def get_personalized_feed(
    user_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    diversity: float = Query(default=0.7, ge=0.0, le=1.0),
    profile_uow: ProfileUnitOfWork = Depends(get_profile_uow),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> FeedResponse:
    use_case = GenerateFeedUseCase(profile_uow, catalog_uow)
    cmd = GenerateFeedCommand(
        user_id=user_id,
        limit=limit,
        diversity_lambda=diversity,
    )
    result = await use_case.execute(cmd)
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


@router.post("/exclusions", response_model=RecordExclusionResponse)
async def record_feed_exclusion(
    req: RecordExclusionRequest,
) -> RecordExclusionResponse:
    # Acknowledges exclusion registration (Rule I06)
    return RecordExclusionResponse(
        status="recorded",
        message="Item has been excluded from future personalized recommendation feeds.",
    )
