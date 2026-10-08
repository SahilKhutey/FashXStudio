from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from fashx.catalog.application.enrich_garment import (
    EnrichGarmentCommand,
    EnrichGarmentUseCase,
)
from fashx.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from fashx.catalog.application.parse_size_chart import (
    ParseSizeChartCommand,
    ParseSizeChartUseCase,
)
from fashx.catalog.quality.quality_gate import CatalogQualityGate
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.database import get_session_factory
from fashx.core.errors import EntityNotFoundError

router = APIRouter(prefix="/catalog", tags=["catalog"])


def get_catalog_uow() -> CatalogUnitOfWork:
    return CatalogUnitOfWork(get_session_factory())


class IngestProductRequest(BaseModel):
    merchant_id: UUID
    source_product_id: str
    title: str
    source_url: str
    category: str
    price_minor: int = Field(ge=0)
    subcategory: str | None = None
    description: str | None = None
    currency: str = "INR"
    in_stock: bool = True
    brand_id: UUID | None = None


class IngestProductResponse(BaseModel):
    merchant_product_id: UUID
    canonical_garment_id: UUID
    offer_id: UUID
    title: str
    category: str
    price_minor: int
    currency: str


class OfferDetail(BaseModel):
    id: UUID
    merchant_id: UUID
    source_product_id: str
    url: str
    price_minor: int
    currency: str
    in_stock: bool


class CanonicalGarmentResponse(BaseModel):
    id: UUID
    brand_id: UUID | None = None
    category: str
    subcategory: str | None = None
    version: int
    offers: list[OfferDetail] = []


class EnrichGarmentResponse(BaseModel):
    enrichment_id: UUID
    garment_id: UUID
    model_version: str
    attributes: dict[str, Any]
    confidence_summary: dict[str, float]
    garment_version: int


class ParseSizeChartRequest(BaseModel):
    storage_key: str = "charts/default.png"
    raw_rows: list[dict[str, Any]]
    default_unit: str = "cm"


class ParseSizeChartResponse(BaseModel):
    size_chart_id: UUID
    garment_id: UUID
    review_status: str
    measurements: list[dict[str, Any]]


class QualityAuditResponse(BaseModel):
    total_garments: int
    completeness_score: float
    category_validity: float
    silhouette_validity: float
    color_validity: float
    passed_gate: bool
    issues: list[str]


@router.post("/products", status_code=status.HTTP_201_CREATED, response_model=IngestProductResponse)
async def ingest_product(
    req: IngestProductRequest,
    uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> IngestProductResponse:
    use_case = IngestMerchantProductUseCase(uow)
    cmd = IngestProductCommand(
        merchant_id=req.merchant_id,
        source_product_id=req.source_product_id,
        title=req.title,
        source_url=req.source_url,
        category=req.category,
        price_minor=req.price_minor,
        subcategory=req.subcategory,
        description=req.description,
        currency=req.currency,
        in_stock=req.in_stock,
        brand_id=req.brand_id,
    )
    result = await use_case.execute(cmd)
    return IngestProductResponse(
        merchant_product_id=result.merchant_product_id,
        canonical_garment_id=result.canonical_garment_id,
        offer_id=result.offer_id,
        title=result.title,
        category=result.category,
        price_minor=result.price_minor,
        currency=result.currency,
    )


@router.post(
    "/garments/{garment_id}/enrich",
    status_code=status.HTTP_200_OK,
    response_model=EnrichGarmentResponse,
)
async def enrich_garment(
    garment_id: UUID,
    uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> EnrichGarmentResponse:
    use_case = EnrichGarmentUseCase(uow)
    cmd = EnrichGarmentCommand(garment_id=garment_id)
    res = await use_case.execute(cmd)
    return EnrichGarmentResponse(
        enrichment_id=res.enrichment_id,
        garment_id=res.garment_id,
        model_version=res.model_version,
        attributes=res.attributes,
        confidence_summary=res.confidence_summary,
        garment_version=res.garment_version,
    )


@router.post(
    "/garments/{garment_id}/size-charts",
    status_code=status.HTTP_201_CREATED,
    response_model=ParseSizeChartResponse,
)
async def parse_size_chart(
    garment_id: UUID,
    req: ParseSizeChartRequest,
    uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> ParseSizeChartResponse:
    use_case = ParseSizeChartUseCase(uow)
    cmd = ParseSizeChartCommand(
        garment_id=garment_id,
        storage_key=req.storage_key,
        raw_rows=req.raw_rows,
        default_unit=req.default_unit,
    )
    res = await use_case.execute(cmd)
    return ParseSizeChartResponse(
        size_chart_id=res.size_chart_id,
        garment_id=res.garment_id,
        review_status=res.review_status,
        measurements=res.measurements,
    )


@router.get("/garments/{garment_id}", response_model=CanonicalGarmentResponse)
async def get_canonical_garment(
    garment_id: UUID,
    uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> CanonicalGarmentResponse:
    async with uow:
        garment = await uow.canonical_garments.get_by_id(garment_id)
        if garment is None:
            raise EntityNotFoundError("CanonicalGarment", garment_id)

        offers = await uow.offers.list_for_garment(garment_id)

        return CanonicalGarmentResponse(
            id=garment.id,
            brand_id=garment.brand_id,
            category=garment.category,
            subcategory=garment.subcategory,
            version=garment.version,
            offers=[
                OfferDetail(
                    id=o.id,
                    merchant_id=o.merchant_id,
                    source_product_id=o.source_product_id,
                    url=o.url,
                    price_minor=o.price_minor,
                    currency=o.currency,
                    in_stock=o.in_stock,
                )
                for o in offers
            ],
        )


@router.get("/quality-audit", response_model=QualityAuditResponse)
async def get_quality_audit(
    uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> QualityAuditResponse:
    async with uow:
        garments = await uow.canonical_garments.list(limit=500)
        items_for_audit: list[dict[str, Any]] = []
        for g in garments:
            enrichment = await uow.enrichments.get_by_garment_id(g.id)
            offers = await uow.offers.list_for_garment(g.id)
            top_price = offers[0].price_minor if offers else 0

            items_for_audit.append(
                {
                    "category": g.category,
                    "attributes": enrichment.attributes_json if enrichment else {},
                    "price_minor": top_price,
                }
            )

        report = CatalogQualityGate.audit_garment_batch(items_for_audit)
        return QualityAuditResponse(
            total_garments=report.total_garments,
            completeness_score=report.completeness_score,
            category_validity=report.category_validity,
            silhouette_validity=report.silhouette_validity,
            color_validity=report.color_validity,
            passed_gate=report.passed_gate,
            issues=report.issues,
        )
