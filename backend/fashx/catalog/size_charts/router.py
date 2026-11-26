"""FastAPI routes for product size charts, revisions, and availability."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from database.models.catalog import MerchantProduct
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.catalog.router import get_catalog_uow
from fashx.catalog.size_charts.enums import AvailabilityStatus, MeasurementUnit
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
from fashx.security.deps import require_role

router = APIRouter(prefix="/products", tags=["size-charts"])


class SizeSystemListItem(BaseModel):
    """Registered regional or category sizing system summary."""

    code: str
    system_type: str
    category: str
    market: str
    display_name: str | None = None
    labels: tuple[str, ...]
    mapping_status: str


async def _resolve_product_target(
    catalog_uow: CatalogUnitOfWork,
    product_id: UUID,
) -> tuple[UUID | None, MerchantProduct | None]:
    """Resolve a MerchantProduct UUID from either MerchantProduct.id or CanonicalGarment.id.

    Raises 404 when neither a MerchantProduct nor an active CanonicalGarment exists.
    """
    prod = await catalog_uow.session.get(MerchantProduct, product_id)
    if prod is not None:
        return prod.id, prod

    garment = await catalog_uow.canonical_garments.get_by_id(product_id)
    if garment is None or not garment.active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found.",
        )

    offers = await catalog_uow.offers.list_for_garment(product_id)
    for offer in offers:
        if (
            getattr(offer, "status", "ACTIVE") == "ACTIVE"
            and getattr(offer, "takedown_status", "NONE") == "NONE"
            and offer.merchant_product_id is not None
        ):
            return offer.merchant_product_id, None

    return None, None


@router.get(
    "/{product_id}/size-chart",
    response_model=ProductSizeChartResponse | SizeChartUnavailableResponse,
)
async def get_product_size_chart(
    product_id: UUID,
    unit: MeasurementUnit | None = Query(
        default=None, description="Preferred unit for display (CM/INCH)"
    ),
    system: str | None = Query(
        default=None, description="Preferred target sizing system (e.g. US, UK, EU)"
    ),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> Any:
    """Retrieve verified merchant-sourced size chart for a given product.

    Returns 200 with verified chart if present, or 200 with an explicit UNAVAILABLE state
    if the merchant has not supplied a verified chart.
    """
    async with catalog_uow:
        target_id, _ = await _resolve_product_target(catalog_uow, product_id)
        service = SizeChartService(catalog_uow.session)
        if target_id is not None:
            chart = await service.get_product_size_chart(
                merchant_product_id=target_id,
                target_unit=unit,
                target_system=system,
            )
            if chart is not None:
                return chart

        return service.get_unavailable_response(product_id)


@router.post(
    "/{product_id}/size-chart",
    response_model=ProductSizeChartResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
async def ingest_product_size_chart(
    product_id: UUID,
    payload: SizeChartRevisionCreate,
    merchant_id: UUID = Query(..., description="ID of the merchant submitting the chart"),
    category: str = Query(default="GENERAL", description="Garment taxonomy category"),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> Any:
    """Ingest, validate, fingerprint, and version a merchant-provided size chart."""
    async with catalog_uow:
        prod = await catalog_uow.session.get(MerchantProduct, product_id)
        if prod is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found.",
            )
        if prod.merchant_id != merchant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Merchant ID does not own the target product.",
            )

        service = SizeChartService(catalog_uow.session)
        try:
            response = await service.ingest_size_chart(
                merchant_product_id=product_id,
                merchant_id=merchant_id,
                payload=payload,
                category=category,
            )
            await catalog_uow.commit()
            return response
        except SizeChartValidationError as e:
            await catalog_uow.commit()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
    async with catalog_uow:
        target_id, _ = await _resolve_product_target(catalog_uow, product_id)
        if target_id is None:
            return []
        service = SizeChartService(catalog_uow.session)
        return await service.list_product_revisions(target_id)


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
    async with catalog_uow:
        target_id, _ = await _resolve_product_target(catalog_uow, product_id)
        if target_id is None:
            return ProductVariantAvailability(
                merchant_product_id=product_id,
                overall_status=AvailabilityStatus.UNKNOWN,
                variants=[],
            )
        service = SizeChartService(catalog_uow.session)
        return await service.get_variant_availability(target_id)


# Size systems catalog
systems_router = APIRouter(prefix="/size-systems", tags=["size-systems"])


@systems_router.get("", response_model=list[SizeSystemListItem])
async def list_registered_size_systems() -> list[SizeSystemListItem]:
    """List all registered regional and category sizing systems."""
    seen: set[str] = set()
    results: list[SizeSystemListItem] = []
    for sys in SYSTEMS.values():
        if sys.code in seen:
            continue
        seen.add(sys.code)
        results.append(
            SizeSystemListItem(
                code=sys.code,
                system_type=sys.system_type,
                category=sys.category,
                market=sys.market,
                display_name=sys.display_name,
                labels=sys.labels,
                mapping_status=sys.mapping_status.value,
            )
        )
    results.sort(key=lambda item: item.code)
    return results
