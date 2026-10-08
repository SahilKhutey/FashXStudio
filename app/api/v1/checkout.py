from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.core.bootstrap import register_core_services
from app.core.context import CoreContext
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.runtime import get_core_runtime
from fashx.domain.checkout.entities import (
    CheckoutSession,
)
from fashx.domain.checkout.service import CheckoutService

from .checkout_schemas import (
    CheckoutCreateRequest,
    CheckoutResponse,
)

router = APIRouter(
    prefix="/checkout",
    tags=["checkout"],
)


def get_checkout_service() -> CheckoutService:
    register_core_services()
    return get_core_runtime().registry.get(
        "checkout_service"
    )


@router.post(
    "",
    response_model=CheckoutResponse,
    status_code=201,
)
async def create_checkout(
    payload: CheckoutCreateRequest,
    service: CheckoutService = Depends(
        get_checkout_service
    ),
):
    try:
        checkout = CheckoutSession(
            cart_id=payload.cart_id,
            customer_id=payload.customer_id,
            currency=payload.currency,
        )

        result = await service.create_checkout(
            context=CoreContext.create(),
            checkout=checkout,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return CheckoutResponse(
        id=result.id,
        cart_id=result.cart_id,
        customer_id=result.customer_id,
        status=result.status.value,
        currency=result.currency,
        order_id=result.order_id,
    )


@router.post(
    "/{checkout_id}/validate",
    response_model=CheckoutResponse,
)
async def validate_checkout(
    checkout_id: UUID,
    service: CheckoutService = Depends(
        get_checkout_service
    ),
):
    try:
        result = await service.validate_checkout(
            context=CoreContext.create(),
            checkout_id=checkout_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return CheckoutResponse(
        id=result.id,
        cart_id=result.cart_id,
        customer_id=result.customer_id,
        status=result.status.value,
        currency=result.currency,
        order_id=result.order_id,
    )
