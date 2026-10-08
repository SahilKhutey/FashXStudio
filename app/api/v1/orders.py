from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.core.bootstrap import register_core_services
from app.core.errors import NotFoundError
from app.core.runtime import get_core_runtime
from fashx.domain.order.service import OrderService

from .order_schemas import (
    OrderResponse,
)

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)


def get_order_service() -> OrderService:
    register_core_services()
    return get_core_runtime().registry.get(
        "order_service"
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
async def get_order(
    order_id: UUID,
    service: OrderService = Depends(
        get_order_service
    ),
):
    try:
        order = await service.get_order(
            order_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        customer_id=order.customer_id,
        status=order.status.value,
        currency=order.currency,
        subtotal=order.subtotal,
        discount_total=order.discount_total,
        shipping_total=order.shipping_total,
        tax_total=order.tax_total,
        grand_total=order.grand_total,
    )
