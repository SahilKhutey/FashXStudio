from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from database.models.catalog import MerchantProduct
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.catalog.router import get_catalog_uow
from fashx.catalog.size_charts.schemas import (
    MerchantSizeChartResponse,
    SizeChartUnavailableResponse,
)
from fashx.catalog.size_charts.service import SizeChartService

router = APIRouter(prefix="/products", tags=["size-charts"])


@router.get(
    "/{product_id}/size-chart",
    response_model=MerchantSizeChartResponse | SizeChartUnavailableResponse,
)
async def get_product_size_chart(
    product_id: UUID,
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> Any:
    """Retrieve verified merchant-sourced size chart for a given product or canonical garment.

    Returns 200 with verified chart if present, or 200 with an explicit UNAVAILABLE state
    if the merchant has not supplied a verified chart.
    """
    service = SizeChartService()
    async with catalog_uow:
        # Check canonical garment or merchant product
        garment = await catalog_uow.canonical_garments.get_by_id(product_id)
        if garment is None:
            # Check merchant product
            prod = await catalog_uow.session.get(MerchantProduct, product_id)
            if prod is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product '{product_id}' not found.",
                )

    # Default fail-closed unavailable response when no verified chart is attached
    return service.get_unavailable_response(product_id)
