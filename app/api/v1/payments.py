from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.bootstrap import register_core_services
from app.core.context import CoreContext
from app.core.errors import NotFoundError
from app.core.runtime import get_core_runtime
from fashx.domain.payments.entities import Payment
from fashx.domain.payments.service import PaymentService

from .payment_schemas import (
    PaymentAuthorizeRequest,
    PaymentCreateRequest,
    PaymentResponse,
)

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
)


def get_payment_service() -> PaymentService:
    register_core_services()
    return get_core_runtime().registry.get(
        "payment_service"
    )


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    payload: PaymentCreateRequest,
    service: PaymentService = Depends(
        get_payment_service
    ),
):
    register_core_services()
    order_repository = (
        get_core_runtime()
        .registry
        .get("order_repository")
    )

    order = await order_repository.get(
        payload.order_id
    )

    if order is None:
        raise NotFoundError(
            "Order was not found.",
            {"order_id": str(payload.order_id)},
        )

    payment = Payment(
        order_id=order.id,
        amount=order.total,
        currency=order.currency,
        idempotency_key=payload.idempotency_key,
    )

    result = await service.create_payment(
        context=CoreContext.create(),
        payment=payment,
    )

    return PaymentResponse(
        id=result.id,
        order_id=result.order_id,
        amount=result.amount,
        currency=result.currency,
        status=result.status.value,
        provider=result.provider,
    )


@router.post(
    "/{payment_id}/authorize",
    response_model=PaymentResponse,
)
async def authorize_payment(
    payment_id: UUID,
    payload: PaymentAuthorizeRequest,
    service: PaymentService = Depends(
        get_payment_service
    ),
):
    result = await service.authorize(
        context=CoreContext.create(),
        payment_id=payment_id,
        payment_method=payload.payment_method,
    )

    return PaymentResponse(
        id=result.id,
        order_id=result.order_id,
        amount=result.amount,
        currency=result.currency,
        status=result.status.value,
        provider=result.provider,
    )


@router.post(
    "/{payment_id}/capture",
    response_model=PaymentResponse,
)
async def capture_payment(
    payment_id: UUID,
    service: PaymentService = Depends(
        get_payment_service
    ),
):
    result = await service.capture(
        context=CoreContext.create(),
        payment_id=payment_id,
    )

    return PaymentResponse(
        id=result.id,
        order_id=result.order_id,
        amount=result.amount,
        currency=result.currency,
        status=result.status.value,
        provider=result.provider,
    )
