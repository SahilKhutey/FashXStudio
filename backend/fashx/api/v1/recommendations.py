from fastapi import APIRouter, Depends, HTTPException

from fashx.core.bootstrap import register_core_services
from fashx.core.errors import ValidationError
from fashx.core.runtime import get_core_runtime
from fashx.domain.recommendations.recommendation_context import (
    RecommendationContext,
)
from fashx.domain.recommendations.service import (
    RecommendationService,
)

from .recommendation_schemas import (
    RecommendationExplanationResponse,
    RecommendationItemResponse,
    RecommendationRequest,
    RecommendationResponse,
)

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)


def get_recommendation_service() -> RecommendationService:
    register_core_services()
    return get_core_runtime().registry.get("recommendation_service")


@router.post(
    "",
    response_model=RecommendationResponse,
)
async def recommend(
    payload: RecommendationRequest,
    service: RecommendationService = Depends(get_recommendation_service),
):
    try:
        context = RecommendationContext(
            customer_id=payload.customer_id,
            region=payload.region,
            currency=payload.currency,
            category=payload.category,
            brand=payload.brand,
            style=payload.style,
            color=payload.color,
            material=payload.material,
            occasion=payload.occasion,
            min_price=payload.min_price,
            max_price=payload.max_price,
            limit=payload.limit,
            exclude_product_ids=tuple(payload.exclude_product_ids),
        )

        result = await service.recommend(context=context)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return RecommendationResponse(
        items=[
            RecommendationItemResponse(
                product_id=item.product_id,
                variant_id=item.variant_id,
                listing_id=item.listing_id,
                score=item.score,
                rank=item.rank,
                explanations=[
                    RecommendationExplanationResponse(
                        reason=ex.reason.value,
                        score=ex.score,
                        message=ex.message,
                    )
                    for ex in item.explanations
                ],
            )
            for item in result.items
        ],
        total_candidates=result.total_candidates,
        engine_version=result.engine_version,
    )
