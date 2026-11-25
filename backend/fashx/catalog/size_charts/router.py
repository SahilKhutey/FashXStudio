"""FastAPI routes for product size charts, revisions, and availability."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from database.models.catalog import MerchantProduct
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.catalog.router import get_catalog_uow
from fashx.catalog.size_charts.enums import MeasurementUnit
from fashx.catalog.size_charts.errors import SizeChartValidationError
from fashx.catalog.size_charts.schemas import (
    ProductSizeChartResponse,
    ProductVariantAvailability,
    SizeChartRevisionCreate,
    SizeChartRevisionSummary,
    SizeChartUnavailableResponse,
)
from fashx.catalog.size_charts.service import SizeChartService
from fashx.catalog.size_charts.size_systems import SYSTEMS

router = APIRouter(prefix="/products", tags=["size-charts"])


@router.get(
    "/{product_id}/size-chart",
    response_model=ProductSizeChartResponse | SizeChartUnavailableResponse,
)
async def get_product_size_chart(
    product_id: UUID,
    unit: MeasurementUnit | None = Query(default=None, description="Preferred unit for display (CM/INCH)"),
    system: str | None = Query(default=None, description="Preferred target sizing system (e.g. US, UK, EU)"),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> Any:
    """Retrieve verified merchant-sourced size chart for a given product.

    Returns 200 with verified chart if present, or 200 with an explicit UNAVAILABLE state
    if the merchant has not supplied a verified chart.
    """
    service = SizeChartService()
    async with catalog_uow:
        # Check canonical garment or merchant product
        garment = await catalog_uow.canonical_garments.get_by_id(product_id)
        if garment is None:
            prod = await catalog_uow.session.get(MerchantProduct, product_id)
            if prod is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product '{product_id}' not found.",
                )

    chart = await service.get_product_size_chart(
        merchant_product_id=product_id, target_unit=unit, target_system=system
    )
    if chart is not None:
        return chart

    # Default fail-closed unavailable response when no verified chart is attached
    return service.get_unavailable_response(product_id)


@router.post(
    "/{product_id}/size-chart",
    response_model=ProductSizeChartResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_product_size_chart(
    product_id: UUID,
    payload: SizeChartRevisionCreate,
    merchant_id: UUID = Query(..., description="ID of the merchant submitting the chart"),
    category: str = Query(default="GENERAL", description="Garment taxonomy category"),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> Any:
    """Ingest, validate, fingerprint, and version a merchant-provided size chart."""
    service = SizeChartService()
    async with catalog_uow:
        prod = await catalog_uow.session.get(MerchantProduct, product_id)
        if prod is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found.",
            )

    try:
        response = await service.ingest_size_chart(
            merchant_product_id=product_id,
            merchant_id=merchant_id,
            payload=payload,
            category=category,
        )
        return response
    except SizeChartValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


@router.get(
    "/{product_id}/size-chart/revisions",
    response_model=list[SizeChartRevisionSummary],
)
async def list_size_chart_revisions(
    product_id: UUID,
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> Any:
    """List historical revisions and fingerprints for a product's size chart."""
    service = SizeChartService()
    async with catalog_uow:
        prod = await catalog_uow.session.get(MerchantProduct, product_id)
        if prod is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found.",
            )

    return await service.list_product_revisions(product_id)


@router.get(
    "/{product_id}/variants",
    response_model=ProductVariantAvailability,
)
@router.get(
    "/{product_id}/availability",
    response_model=ProductVariantAvailability,
)
async def get_product_variant_availability(
    product_id: UUID,
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> Any:
    """Retrieve current purchasable variant availability and stock freshness."""
    service = SizeChartService()
    async with catalog_uow:
        prod = await catalog_uow.session.get(MerchantProduct, product_id)
        if prod is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found.",
            )

    return await service.get_variant_availability(product_id)


# Size systems catalog
systems_router = APIRouter(prefix="/size-systems", tags=["size-systems"])


@systems_router.get("", response_model=list[dict[str, Any]])
async def list_registered_size_systems() -> list[dict[str, Any]]:
    """List all registered regional and category sizing systems."""
    results = []
    for _code, sys in SYSTEMS.items():
        results.append(
            {
                "code": sys.code,
                "system_type": sys.system_type,
                "category": sys.category,
                "market": sys.market,
                "display_name": sys.display_name,
                "labels": sys.labels,
                "mapping_status": sys.mapping_status.value,
            }
        )
    return results
