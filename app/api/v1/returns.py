from fastapi import APIRouter, Depends

from app.core.bootstrap import register_core_services
from app.core.context import CoreContext
from app.core.runtime import get_core_runtime
from app.domain.returns.entities import (
    CancellationRequest,
    Refund,
    ReturnLine,
    ReturnRequest,
)
from app.domain.returns.enums import (
    RefundReason,
    ReturnReason,
)
from app.domain.returns.service import (
    ReturnsService,
)

from .returns_schemas import (
    CancellationCreateRequest,
    CancellationResponse,
    RefundCreateRequest,
    RefundResponse,
    ReturnCreateRequest,
    ReturnResponse,
)

router = APIRouter(
    prefix="/returns",
    tags=["returns"],
)


def get_returns_service() -> ReturnsService:
    register_core_services()
    return get_core_runtime().registry.get(
        "returns_service"
    )


@router.post(
    "",
    response_model=ReturnResponse,
    status_code=201,
)
async def create_return(
    payload: ReturnCreateRequest,
    service: ReturnsService = Depends(
        get_returns_service
    ),
):
    request = ReturnRequest(
        order_id=payload.order_id,
        customer_id=payload.customer_id,
        reason=ReturnReason(payload.reason),
        notes=payload.notes,
    )

    lines = [
        ReturnLine(
            order_line_id=line.order_line_id,
            product_id=line.product_id,
            variant_id=line.variant_id,
            quantity=line.quantity,
            refund_amount=line.refund_amount,
        )
        for line in payload.lines
    ]

    result = await service.request_return(
        context=CoreContext.create(),
        request=request,
        lines=lines,
    )

    return ReturnResponse(
        id=result.id,
        order_id=result.order_id,
        status=result.status.value,
    )


@router.post(
    "/cancellations",
    response_model=CancellationResponse,
    status_code=201,
)
async def create_cancellation(
    payload: CancellationCreateRequest,
    service: ReturnsService = Depends(
        get_returns_service
    ),
):
    request = CancellationRequest(
        order_id=payload.order_id,
        customer_id=payload.customer_id,
        reason=payload.reason,
    )

    result = await service.request_cancellation(
        context=CoreContext.create(),
        request=request,
    )

    return CancellationResponse(
        id=result.id,
        order_id=result.order_id,
        status=result.status.value,
    )


@router.post(
    "/refunds",
    response_model=RefundResponse,
    status_code=201,
)
async def create_refund(
    payload: RefundCreateRequest,
    service: ReturnsService = Depends(
        get_returns_service
    ),
):
    refund = Refund(
        order_id=payload.order_id,
        return_id=payload.return_id,
        payment_id=payload.payment_id,
        amount=payload.amount,
        currency=payload.currency,
        reason=RefundReason(payload.reason),
    )

    result = await service.request_refund(
        context=CoreContext.create(),
        refund=refund,
    )

    return RefundResponse(
        id=result.id,
        order_id=result.order_id,
        amount=result.amount,
        currency=result.currency,
        status=result.status.value,
    )
