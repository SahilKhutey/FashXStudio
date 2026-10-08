from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.bootstrap import register_core_services
from app.core.context import CoreContext
from app.core.runtime import get_core_runtime
from fashx.domain.inventory.entities import (
    InventoryItem,
    StockLocation,
)
from fashx.domain.inventory.service import (
    InventoryService,
)

from .inventory_schemas import (
    InventoryCreateRequest,
    InventoryResponse,
    InventoryStatusRequest,
    StockAdjustmentRequest,
    StockLocationCreateRequest,
    StockLocationResponse,
)

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
)


def get_inventory_service() -> InventoryService:
    register_core_services()
    return get_core_runtime().registry.get(
        "inventory_service"
    )


def inventory_response(
    item: InventoryItem,
) -> InventoryResponse:
    return InventoryResponse(
        id=item.id,
        variant_id=item.variant_id,
        seller_id=item.seller_id,
        location_id=item.location_id,
        status=item.status,
        on_hand=item.on_hand,
        reserved=item.reserved,
        incoming=item.incoming,
        available=item.available,
        availability=item.availability,
        low_stock_threshold=item.low_stock_threshold,
        version=item.version,
    )


@router.post(
    "/locations",
    response_model=StockLocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_location(
    payload: StockLocationCreateRequest,
    service: InventoryService = Depends(
        get_inventory_service
    ),
):
    location = StockLocation(
        seller_id=payload.seller_id,
        name=payload.name,
        code=payload.code,
        location_type=payload.location_type,
        region=payload.region,
        metadata=payload.metadata,
    )

    result = await service.create_location(
        context=CoreContext.create(),
        location=location,
    )

    return StockLocationResponse(
        id=result.id,
        seller_id=result.seller_id,
        name=result.name,
        code=result.code,
        location_type=result.location_type,
        region=result.region,
        version=result.version,
    )


@router.post(
    "/items",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_inventory(
    payload: InventoryCreateRequest,
    service: InventoryService = Depends(
        get_inventory_service
    ),
):
    item = InventoryItem(
        variant_id=payload.variant_id,
        seller_id=payload.seller_id,
        location_id=payload.location_id,
        on_hand=payload.on_hand,
        incoming=payload.incoming,
        low_stock_threshold=payload.low_stock_threshold,
        metadata=payload.metadata,
    )

    result = await service.create_inventory(
        context=CoreContext.create(),
        inventory=item,
    )

    return inventory_response(result)


@router.get(
    "/items/{inventory_id}",
    response_model=InventoryResponse,
)
async def get_inventory(
    inventory_id: UUID,
    service: InventoryService = Depends(
        get_inventory_service
    ),
):
    result = await service.get_inventory(
        inventory_id
    )

    return inventory_response(result)


@router.get(
    "/variants/{variant_id}",
    response_model=list[InventoryResponse],
)
async def variant_inventory(
    variant_id: UUID,
    service: InventoryService = Depends(
        get_inventory_service
    ),
):
    results = await service.list_variant_inventory(
        variant_id
    )

    return [
        inventory_response(item)
        for item in results
    ]


@router.post(
    "/items/{inventory_id}/adjust",
    response_model=InventoryResponse,
)
async def adjust_stock(
    inventory_id: UUID,
    payload: StockAdjustmentRequest,
    service: InventoryService = Depends(
        get_inventory_service
    ),
):
    result = await service.adjust_stock(
        context=CoreContext.create(),
        inventory_id=inventory_id,
        adjustment_type=payload.adjustment_type,
        quantity=payload.quantity,
        reason=payload.reason,
    )

    return inventory_response(result)


@router.post(
    "/items/{inventory_id}/status",
    response_model=InventoryResponse,
)
async def change_status(
    inventory_id: UUID,
    payload: InventoryStatusRequest,
    service: InventoryService = Depends(
        get_inventory_service
    ),
):
    result = await service.change_status(
        context=CoreContext.create(),
        inventory_id=inventory_id,
        target=payload.status,
    )

    return inventory_response(result)
