from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.bootstrap import register_core_services
from app.core.context import CoreContext
from app.core.runtime import get_core_runtime
from fashx.domain.pricing.enums import Currency
from fashx.domain.pricing.money import money
from fashx.domain.promotions.entities import (
    Offer,
    Promotion,
)
from fashx.domain.promotions.service import (
    PromotionService,
)

from .promotion_schemas import (
    CalculateOfferRequest,
    OfferCalculationResponse,
    OfferCreateRequest,
    OfferResponse,
    OfferStatusRequest,
    PromotionCreateRequest,
    PromotionResponse,
    PromotionStatusRequest,
)

router = APIRouter(
    prefix="/promotions",
    tags=["promotions"],
)


def get_promotion_service() -> PromotionService:
    register_core_services()
    return get_core_runtime().registry.get(
        "promotion_service"
    )


def promotion_response(
    promotion: Promotion,
) -> PromotionResponse:
    return PromotionResponse(
        id=promotion.id,
        name=promotion.name,
        code=promotion.code,
        status=promotion.status,
        scope=promotion.scope,
        discount_type=promotion.discount_type,
        discount_value=promotion.discount_value,
        maximum_discount=promotion.maximum_discount,
        minimum_purchase_value=promotion.minimum_purchase_value,
        start_at=promotion.start_at,
        end_at=promotion.end_at,
        version=promotion.version,
    )


def offer_response(
    offer: Offer,
) -> OfferResponse:
    return OfferResponse(
        id=offer.id,
        promotion_id=offer.promotion_id,
        product_id=offer.product_id,
        variant_id=offer.variant_id,
        listing_id=offer.listing_id,
        status=offer.status,
        version=offer.version,
    )


@router.post(
    "",
    response_model=PromotionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_promotion(
    payload: PromotionCreateRequest,
    service: PromotionService = Depends(
        get_promotion_service
    ),
):
    promotion = Promotion(
        name=payload.name,
        code=payload.code,
        scope=payload.scope,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        maximum_discount=payload.maximum_discount,
        minimum_purchase_value=payload.minimum_purchase_value,
        start_at=payload.start_at,
        end_at=payload.end_at,
        usage_limit=payload.usage_limit,
        per_customer_limit=payload.per_customer_limit,
        metadata=payload.metadata,
    )

    result = await service.create_promotion(
        context=CoreContext.create(),
        promotion=promotion,
    )

    return promotion_response(result)


@router.post(
    "/{promotion_id}/status",
    response_model=PromotionResponse,
)
async def change_promotion_status(
    promotion_id: UUID,
    payload: PromotionStatusRequest,
    service: PromotionService = Depends(
        get_promotion_service
    ),
):
    result = await service.change_promotion_status(
        context=CoreContext.create(),
        promotion_id=promotion_id,
        target=payload.status,
    )

    return promotion_response(result)


@router.post(
    "/offers",
    response_model=OfferResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_offer(
    payload: OfferCreateRequest,
    service: PromotionService = Depends(
        get_promotion_service
    ),
):
    offer = Offer(
        promotion_id=payload.promotion_id,
        product_id=payload.product_id,
        variant_id=payload.variant_id,
        listing_id=payload.listing_id,
        metadata=payload.metadata,
    )

    result = await service.create_offer(
        context=CoreContext.create(),
        offer=offer,
    )

    return offer_response(result)


@router.post(
    "/offers/{offer_id}/status",
    response_model=OfferResponse,
)
async def change_offer_status(
    offer_id: UUID,
    payload: OfferStatusRequest,
    service: PromotionService = Depends(
        get_promotion_service
    ),
):
    result = await service.change_offer_status(
        context=CoreContext.create(),
        offer_id=offer_id,
        target=payload.status,
    )

    return offer_response(result)


@router.post(
    "/offers/{offer_id}/calculate",
    response_model=OfferCalculationResponse,
)
async def calculate_offer(
    offer_id: UUID,
    payload: CalculateOfferRequest,
    service: PromotionService = Depends(
        get_promotion_service
    ),
):
    calc = await service.calculate_offer(
        context=CoreContext.create(),
        offer_id=offer_id,
        base_price=money(payload.amount, Currency(payload.currency)),
        purchase_value=payload.purchase_value,
    )

    return OfferCalculationResponse(
        base_price_amount=calc.base_price.amount,
        base_price_currency=str(calc.base_price.currency),
        discount_amount=calc.discount.amount,
        discount_currency=str(calc.discount.currency),
        final_price_amount=calc.final_price.amount,
        final_price_currency=str(calc.final_price.currency),
        promotion_id=calc.promotion_id,
        offer_id=calc.offer_id,
    )
