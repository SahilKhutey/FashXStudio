"""FastAPI v1 endpoints for Phase 08.4 Personalized Product Ranking."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query, status

from fashx.catalog.taxonomy.loader import get_taxonomy_registry
from fashx.ranking.cache import RankingCache
from fashx.ranking.category import RegistryTaxonomyAdapter
from fashx.ranking.config import (
    RANKING_CONFIGS,
    RankingConfigResponse,
    get_ranking_config,
)
from fashx.ranking.contracts import (
    ProductFeedbackCreate,
    ProductFeedbackResponse,
    RankedProductsResponse,
    RankingRequest,
    ShopperRankingPreferencesResponse,
    ShopperRankingPreferencesUpdate,
)
from fashx.ranking.repository import InMemoryRankingStore
from fashx.ranking.service import PersonalizedRankingService
from fashx.security.deps import Principal, get_principal

router = APIRouter(tags=["ranking"])
admin_router = APIRouter(tags=["ranking-admin"])

_SHARED_CACHE = RankingCache()
_SHARED_STORE = InMemoryRankingStore()


def get_ranking_store() -> InMemoryRankingStore:
    """Dependency providing the ranking candidate/preference/feedback store."""
    return _SHARED_STORE


def get_ranking_service() -> PersonalizedRankingService:
    """Dependency providing the PersonalizedRankingService backed by Phase 06 taxonomy."""
    taxonomy = RegistryTaxonomyAdapter(get_taxonomy_registry())
    return PersonalizedRankingService(taxonomy=taxonomy, cache=_SHARED_CACHE)


@router.post("/ranking/products", response_model=RankedProductsResponse)
async def rank_products(
    payload: RankingRequest,
    principal: Principal = Depends(get_principal),
    store: InMemoryRankingStore = Depends(get_ranking_store),
    service: PersonalizedRankingService = Depends(get_ranking_service),
) -> RankedProductsResponse:
    """Return personalized (or baseline) ranked eligible products for the authenticated shopper."""
    try:
        get_ranking_config(payload.ranking_version)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    shopper_id = str(principal.user_id)
    snapshot = store.build_shopper_snapshot(shopper_id)
    candidates = store.retrieve(payload.context)
    return service.rank(
        shopper_profile=snapshot,
        candidates=candidates,
        context=payload.context,
        ranking_version=payload.ranking_version,
    )


@admin_router.post("/ranking/preview", response_model=RankedProductsResponse)
async def preview_ranking(
    payload: RankingRequest,
    shopper_id: str | None = Query(default=None),
    principal: Principal = Depends(get_principal),
    store: InMemoryRankingStore = Depends(get_ranking_store),
    service: PersonalizedRankingService = Depends(get_ranking_service),
) -> RankedProductsResponse:
    """Internal/admin preview endpoint for inspecting ranking behaviour."""
    try:
        get_ranking_config(payload.ranking_version)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    target_id = shopper_id or str(principal.user_id)
    snapshot = store.build_shopper_snapshot(target_id)
    candidates = store.retrieve(payload.context)
    return service.rank(
        shopper_profile=snapshot,
        candidates=candidates,
        context=payload.context,
        ranking_version=payload.ranking_version,
        use_cache=False,
    )


@router.get("/ranking/config", response_model=RankingConfigResponse)
async def get_ranking_configuration(
    ranking_version: str = Query(default="personalized-v1"),
    _principal: Principal = Depends(get_principal),
) -> RankingConfigResponse:
    """Read active versioned ranking configuration and weights."""
    try:
        cfg = get_ranking_config(ranking_version)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return RankingConfigResponse(
        ranking_version=cfg.ranking_version,
        config_version=cfg.config_version,
        taxonomy_version=cfg.taxonomy_version,
        supported_versions=sorted(RANKING_CONFIGS),
        weights={k: float(v) for k, v in asdict(cfg.weights).items()},
        max_availability_age_seconds=cfg.max_availability_age_seconds,
        cache_ttl_seconds=cfg.cache_ttl_seconds,
    )


@router.post(
    "/products/{product_id}/feedback",
    response_model=ProductFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_product_feedback(
    product_id: str,
    payload: ProductFeedbackCreate,
    principal: Principal = Depends(get_principal),
    store: InMemoryRankingStore = Depends(get_ranking_store),
    service: PersonalizedRankingService = Depends(get_ranking_service),
) -> ProductFeedbackResponse:
    """Submit explicit product feedback for the authenticated shopper."""
    shopper_id = str(principal.user_id)
    res = store.submit_feedback(shopper_id, product_id, payload.feedback_type)
    service.cache.invalidate_shopper(shopper_id)
    return res


@router.get("/products/{product_id}/feedback", response_model=list[ProductFeedbackResponse])
async def get_product_feedback(
    product_id: str,
    principal: Principal = Depends(get_principal),
    store: InMemoryRankingStore = Depends(get_ranking_store),
) -> list[ProductFeedbackResponse]:
    """Retrieve explicit feedback submitted by the authenticated shopper for a product."""
    return store.get_feedback(str(principal.user_id), product_id)


@router.delete("/products/{product_id}/feedback")
async def delete_product_feedback(
    product_id: str,
    principal: Principal = Depends(get_principal),
    store: InMemoryRankingStore = Depends(get_ranking_store),
    service: PersonalizedRankingService = Depends(get_ranking_service),
) -> dict[str, object]:
    """Withdraw explicit product feedback for the authenticated shopper."""
    shopper_id = str(principal.user_id)
    removed = store.delete_feedback(shopper_id, product_id)
    service.cache.invalidate_shopper(shopper_id)
    return {"product_id": product_id, "removed_count": removed}


@router.get("/shopper/preferences", response_model=ShopperRankingPreferencesResponse)
async def get_shopper_ranking_preferences(
    principal: Principal = Depends(get_principal),
    store: InMemoryRankingStore = Depends(get_ranking_store),
) -> ShopperRankingPreferencesResponse:
    """Retrieve the authenticated shopper's ranking preferences."""
    return store.get_preferences(str(principal.user_id))


@router.patch("/shopper/preferences", response_model=ShopperRankingPreferencesResponse)
async def update_shopper_ranking_preferences(
    payload: ShopperRankingPreferencesUpdate,
    principal: Principal = Depends(get_principal),
    store: InMemoryRankingStore = Depends(get_ranking_store),
    service: PersonalizedRankingService = Depends(get_ranking_service),
) -> ShopperRankingPreferencesResponse:
    """Update the authenticated shopper's ranking preferences and invalidate cache."""
    shopper_id = str(principal.user_id)
    updated = store.update_preferences(shopper_id, payload)
    service.cache.invalidate_shopper(shopper_id)
    return updated
