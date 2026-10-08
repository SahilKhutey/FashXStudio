from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from fashx.core.bootstrap import register_core_services
from fashx.core.context import CoreContext
from fashx.core.runtime import get_core_runtime
from fashx.domain.fulfillment.entities import (
    AddressSnapshot,
    Fulfillment,
    FulfillmentLine,
    Shipment,
)
from fashx.domain.fulfillment.enums import (
    ShippingMethod,
)
from fashx.domain.fulfillment.service import (
    FulfillmentService,
)

from .fulfillment_schemas import (
    FulfillmentCreateRequest,
    FulfillmentResponse,
    ShipmentCreateRequest,
    ShipmentResponse,
)

router = APIRouter(
    prefix="/fulfillment",
    tags=["fulfillment"],
)


def get_fulfillment_service() -> FulfillmentService:
    register_core_services()
    return get_core_runtime().registry.get(
        "fulfillment_service"
    )


@router.post(
    "",
    response_model=FulfillmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_fulfillment(
    payload: FulfillmentCreateRequest,
    service: FulfillmentService = Depends(
        get_fulfillment_service
    ),
):
    address = AddressSnapshot(
        recipient_name=payload.address.recipient_name,
        address_line_1=payload.address.address_line_1,
        address_line_2=payload.address.address_line_2,
        city=payload.address.city,
        state=payload.address.state,
        postal_code=payload.address.postal_code,
        country=payload.address.country,
        phone=payload.address.phone,
    )

    fulfillment = Fulfillment(
        order_id=payload.order_id,
        shipping_method=ShippingMethod(
            payload.shipping_method
        ),
        address=address,
    )

    lines = [
        FulfillmentLine(
            order_line_id=line.order_line_id,
            product_id=line.product_id,
            variant_id=line.variant_id,
            quantity=line.quantity,
        )
        for line in payload.lines
    ]

    result = await service.create_fulfillment(
        context=CoreContext.create(),
        fulfillment=fulfillment,
        lines=lines,
    )

    return FulfillmentResponse(
        id=result.id,
        order_id=result.order_id,
        status=result.status.value,
    )


@router.post(
    "/{fulfillment_id}/shipments",
    response_model=ShipmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_shipment(
    fulfillment_id: UUID,
    payload: ShipmentCreateRequest,
    service: FulfillmentService = Depends(
        get_fulfillment_service
    ),
):
    shipment = Shipment(
        carrier=payload.carrier,
        shipping_method=ShippingMethod(
            payload.shipping_method
        ),
    )

    result = await service.create_shipment(
        context=CoreContext.create(),
        fulfillment_id=fulfillment_id,
        shipment=shipment,
    )

    return ShipmentResponse(
        id=result.id,
        fulfillment_id=result.fulfillment_id,
        carrier=result.carrier,
        tracking_number=result.tracking_number,
        status=result.status.value,
    )
