from fastapi import APIRouter, Depends, HTTPException

from app.core.bootstrap import register_core_services
from app.core.context import CoreContext
from app.core.errors import NotFoundError, ValidationError
from app.core.runtime import get_core_runtime
from fashx.domain.pricing.entities import (
    Price,
    PricingRule,
)
from fashx.domain.pricing.enums import (
    DiscountType,
    PriceStatus,
    PriceType,
    RuleStatus,
)
from fashx.domain.pricing.rules import (
    PricingContext,
)
from fashx.domain.pricing.service import (
    PricingService,
)

from .pricing_schemas import (
    PriceAdjustmentResponse,
    PriceCalculateRequest,
    PriceCalculationResponse,
    PriceCreateRequest,
    RuleCreateRequest,
)

router = APIRouter(
    prefix="/pricing",
    tags=["pricing"],
)


def get_pricing_service() -> PricingService:
    register_core_services()
    return get_core_runtime().registry.get(
        "pricing_service"
    )


@router.post(
    "/prices",
    status_code=201,
)
async def create_price(
    payload: PriceCreateRequest,
    service: PricingService = Depends(
        get_pricing_service
    ),
):
    try:
        price = Price(
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            listing_id=payload.listing_id,
            amount=payload.amount,
            currency=payload.currency,
            price_type=PriceType(payload.price_type),
            status=PriceStatus(payload.status),
            valid_from=payload.valid_from,
            valid_until=payload.valid_until,
        )

        result = await service.create_price(
            context=CoreContext.create(),
            price=price,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return {
        "id": result.id,
        "amount": result.amount,
        "currency": result.currency,
        "status": result.status.value,
    }


@router.post(
    "/rules",
    status_code=201,
)
async def create_rule(
    payload: RuleCreateRequest,
    service: PricingService = Depends(
        get_pricing_service
    ),
):
    try:
        rule = PricingRule(
            name=payload.name,
            discount_type=DiscountType(payload.discount_type),
            discount_value=payload.discount_value,
            priority=payload.priority,
            status=RuleStatus(payload.status),
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            listing_id=payload.listing_id,
            customer_id=payload.customer_id,
            region=payload.region,
            minimum_quantity=payload.minimum_quantity,
            minimum_cart_value=payload.minimum_cart_value,
            valid_from=payload.valid_from,
            valid_until=payload.valid_until,
        )

        result = await service.create_rule(
            context=CoreContext.create(),
            rule=rule,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return {
        "id": result.id,
        "name": result.name,
        "status": result.status.value,
    }


@router.post(
    "/calculate",
    response_model=PriceCalculationResponse,
)
async def calculate_price(
    payload: PriceCalculateRequest,
    service: PricingService = Depends(
        get_pricing_service
    ),
):
    pricing_context = PricingContext(
        product_id=payload.product_id,
        variant_id=payload.variant_id,
        listing_id=payload.listing_id,
        customer_id=payload.customer_id,
        region=payload.region,
        currency=payload.currency,
        quantity=payload.quantity,
        cart_value=payload.cart_value,
    )

    try:
        result = await service.calculate(
            context=CoreContext.create(),
            pricing_context=pricing_context,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return PriceCalculationResponse(
        original_amount=result.original_amount,
        adjustments=[
            PriceAdjustmentResponse(
                rule_id=item.rule_id,
                description=item.description,
                amount=item.amount,
            )
            for item in result.adjustments
        ],
        final_amount=result.final_amount,
        currency=result.currency,
    )
