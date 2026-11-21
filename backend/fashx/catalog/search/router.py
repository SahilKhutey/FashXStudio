from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog_search import ProductSearchEventRecord, SearchSessionRecord
from fashx.catalog.search.contracts import (
    ProductSearchRequest,
    ProductSearchResponse,
    SearchFacetsResponse,
    SearchInteractionEventRequest,
    SearchSessionResponse,
    SearchSuggestionsResponse,
    SemanticSearchRequest,
    VisualSearchRequest,
)
from fashx.catalog.search.search_service import FashionSearchService
from fashx.catalog.search.suggestions import get_query_suggestions
from fashx.core.database import get_db_session
from fashx.security.deps import Principal, get_optional_principal

router = APIRouter(prefix="/search", tags=["search"])
search_service = FashionSearchService()


@router.get("/products", response_model=ProductSearchResponse)
async def search_products(
    q: str | None = Query(default=None, max_length=200),
    category_id: UUID | None = Query(default=None),
    brand_id: UUID | None = Query(default=None),
    color_id: UUID | None = Query(default=None),
    occasion_id: UUID | None = Query(default=None),
    size: str | None = Query(default=None, max_length=40),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    currency: str = Query(default="INR", min_length=3, max_length=3),
    in_stock: bool | None = Query(default=None),
    sort: Literal[
        "relevance",
        "price_low",
        "price_high",
        "newest",
        "recently_updated",
        "popularity",
        "similarity",
    ] = Query(default="relevance"),
    limit: int = Query(default=20, ge=1, le=50),
    cursor: str | None = Query(default=None, max_length=2048),
    session: AsyncSession = Depends(get_db_session),
    principal: Principal | None = Depends(get_optional_principal),
) -> ProductSearchResponse:
    """Unified shopper search endpoint combining keywords, structured filters, and hybrid ranking."""
    try:
        search_req = ProductSearchRequest(
            q=q,
            category_id=category_id,
            brand_id=brand_id,
            color_id=color_id,
            occasion_id=occasion_id,
            size=size,
            min_price=min_price,
            max_price=max_price,
            currency=currency,
            in_stock=in_stock,
            sort=sort,
            limit=limit,
            cursor=cursor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    user_uuid = UUID(principal.user_id) if principal and principal.user_id else None

    def _sync_search(sync_sess) -> ProductSearchResponse:
        return search_service.search(sync_sess, search_req, user_id=user_uuid)

    try:
        res = await session.run_sync(_sync_search)
        await session.commit()
        return res
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/semantic", response_model=ProductSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal | None = Depends(get_optional_principal),
) -> ProductSearchResponse:
    """Natural-language semantic search retrieving products by stylistic intent and meaning."""
    user_uuid = UUID(principal.user_id) if principal and principal.user_id else None

    def _sync_semantic(sync_sess) -> ProductSearchResponse:
        return search_service.semantic_search(sync_sess, request, user_id=user_uuid)

    try:
        res = await session.run_sync(_sync_semantic)
        await session.commit()
        return res
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/visual", response_model=ProductSearchResponse)
async def visual_search(
    request: VisualSearchRequest,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal | None = Depends(get_optional_principal),
) -> ProductSearchResponse:
    """Visual similarity search matching against Phase 06.3 image embeddings."""
    user_uuid = UUID(principal.user_id) if principal and principal.user_id else None

    def _sync_visual(sync_sess) -> ProductSearchResponse:
        return search_service.visual_search(sync_sess, request, user_id=user_uuid)

    try:
        res = await session.run_sync(_sync_visual)
        await session.commit()
        return res
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/suggestions", response_model=SearchSuggestionsResponse)
async def query_suggestions(
    prefix: str | None = Query(default=None, max_length=100),
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=5, ge=1, le=20),
    session: AsyncSession = Depends(get_db_session),
) -> SearchSuggestionsResponse:
    """Retrieve fast auto-complete query suggestions."""
    target_prefix = prefix or q or ""
    if len(target_prefix) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Prefix must be at least 2 characters",
        )

    def _sync_suggestions(sync_sess) -> list[str]:
        return get_query_suggestions(sync_sess, prefix=target_prefix, limit=limit)

    suggestions = await session.run_sync(_sync_suggestions)
    return SearchSuggestionsResponse(prefix=target_prefix, suggestions=suggestions)


@router.get("/facets", response_model=SearchFacetsResponse)
async def search_facets(
    q: str | None = Query(default=None, max_length=200),
    category_id: UUID | None = Query(default=None),
    brand_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> SearchFacetsResponse:
    """Compute available facet counts for candidate results."""
    search_req = ProductSearchRequest(
        q=q,
        category_id=category_id,
        brand_id=brand_id,
        limit=50,
    )

    def _sync_facets(sync_sess) -> dict[str, list[dict[str, Any]]]:
        res = search_service.search(sync_sess, search_req)
        return res.facets

    facets = await session.run_sync(_sync_facets)
    return SearchFacetsResponse(facets=facets)


@router.get("/sessions/{session_id}", response_model=SearchSessionResponse)
async def get_search_session_page(
    session_id: UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=50),
    session: AsyncSession = Depends(get_db_session),
) -> SearchSessionResponse:
    """Retrieve a stable paginated search result page from a search session snapshot."""
    sess_rec = await session.get(SearchSessionRecord, session_id)
    if sess_rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search session not found")

    candidate_ids = [UUID(cid) for cid in sess_rec.result_ids_json]

    def _sync_hydrate(sync_sess):
        return search_service._hydrate_product_cards(sync_sess, candidate_ids[offset : offset + limit])

    items = await session.run_sync(_sync_hydrate)
    next_cursor = None
    if offset + limit < len(candidate_ids):
        from fashx.catalog.search.pagination import generate_cursor_token

        next_cursor = generate_cursor_token(session_id, offset + limit)

    return SearchSessionResponse(
        session_id=session_id,
        query=sess_rec.query_text,
        total_results=sess_rec.total_results,
        applied_filters=sess_rec.applied_filters_json,
        items=items,
        next_cursor=next_cursor,
    )


@router.post("/events", status_code=status.HTTP_201_CREATED)
async def record_search_event(
    event_req: SearchInteractionEventRequest,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal | None = Depends(get_optional_principal),
) -> dict[str, str]:
    """Record a shopper search interaction event (click, save, handoff)."""
    user_uuid = UUID(principal.user_id) if principal and principal.user_id else None

    event_record = ProductSearchEventRecord(
        session_id=event_req.session_id,
        user_id=user_uuid,
        event_type=event_req.event_type,
        query=event_req.query,
        filter_key=event_req.filter_key,
        filter_value=event_req.filter_value,
        product_id=event_req.product_id,
        merchant_product_id=event_req.merchant_product_id,
        rank_position=event_req.rank_position,
        metadata_json=event_req.metadata_json,
    )
    session.add(event_record)
    await session.commit()
    return {"status": "recorded"}


__all__ = ["router"]
