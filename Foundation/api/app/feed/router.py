from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth.dependencies import current_user_id
from api.app.core.dependencies import db_session
from api.app.feed.application.feed import FeedApplicationService
from api.app.feed.repositories.feed import FeedRepository
from schemas.feed.api import FeedQuery, FeedResponse
from schemas.feed.cursor import InvalidFeedCursor

router = APIRouter(prefix="/api/v1/feed", tags=["feed"])


def get_repository(session: AsyncSession = Depends(db_session)) -> FeedRepository:
    return FeedRepository(session)


def get_service(repository: FeedRepository = Depends(get_repository)) -> FeedApplicationService:
    return FeedApplicationService(repository)


@router.get("/me", response_model=FeedResponse)
async def get_my_feed(
    category: str | None = Query(default=None),
    subcategory: str | None = Query(default=None),
    price_min: int | None = Query(default=None, ge=0),
    price_max: int | None = Query(default=None, ge=0),
    limit: int = Query(default=20, ge=1, le=50),
    cursor: str | None = Query(default=None),
    user_id=Depends(current_user_id),
    service: FeedApplicationService = Depends(get_service),
) -> FeedResponse:
    try:
        return await service.get_feed(
            user_id=user_id,
            query=FeedQuery(
                category=category,
                subcategory=subcategory,
                price_min=price_min,
                price_max=price_max,
                limit=limit,
                cursor=cursor,
            ),
        )
    except InvalidFeedCursor as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
