from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth.dependencies import current_user_id
from api.app.catalog.application.catalog_use_cases import CatalogApplicationService
from api.app.catalog.repositories.catalog import CatalogRepository
from api.app.core.dependencies import db_session
from api.app.core.errors import NotFoundError
from schemas.catalog.detail import CatalogDetail
from schemas.catalog.garment import CanonicalGarment, MerchantOffer
from schemas.catalog.garment_image import GarmentImage
from schemas.catalog.intake import CatalogIntakeRequest, CatalogIntakeResponse
from schemas.catalog.search import CatalogItemSummary, CatalogSearchResponse

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


def get_repository(session: AsyncSession = Depends(db_session)) -> CatalogRepository:
    return CatalogRepository(session)


@router.get("/search", response_model=CatalogSearchResponse)
async def search_catalog(
    category: str | None = Query(default=None),
    subcategory: str | None = Query(default=None),
    price_min: int | None = Query(default=None, ge=0),
    price_max: int | None = Query(default=None, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: UUID | None = Query(default=None),
    _: UUID = Depends(current_user_id),
    repository: CatalogRepository = Depends(get_repository),
) -> CatalogSearchResponse:
    if price_min is not None and price_max is not None and price_min > price_max:
        raise HTTPException(status_code=400, detail="price_min cannot exceed price_max")
    garments = await repository.search_garments(
        category=category,
        subcategory=subcategory,
        price_min=price_min,
        price_max=price_max,
        limit=limit,
        cursor_id=cursor,
    )
    next_cursor = str(garments[-1].id) if len(garments) == limit else None
    return CatalogSearchResponse(
        products=[CatalogItemSummary.model_validate(item, from_attributes=True) for item in garments],
        next_cursor=next_cursor,
    )


@router.get("/{product_id}", response_model=CatalogDetail)
async def get_catalog_item(
    product_id: UUID,
    _: UUID = Depends(current_user_id),
    repository: CatalogRepository = Depends(get_repository),
) -> CatalogDetail:
    garment = await repository.get_garment(product_id)
    if garment is None:
        raise NotFoundError("Catalog product not found")
    images = await repository.get_images(product_id)
    offers = await repository.get_offers(product_id)
    return CatalogDetail(
        garment=CanonicalGarment.model_validate(garment, from_attributes=True),
        images=[GarmentImage.model_validate(image, from_attributes=True) for image in images],
        offers=[MerchantOffer.model_validate(offer, from_attributes=True) for offer in offers],
    )


@router.post("/intake", response_model=CatalogIntakeResponse)
async def catalog_intake(
    payload: CatalogIntakeRequest,
    repository: CatalogRepository = Depends(get_repository),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> CatalogIntakeResponse:
    # Foundation 3 uses a development token gate. A service identity layer replaces this
    # header before multi-service production deployment.
    from api.app.core.settings import get_settings
    settings = get_settings()
    if not settings.internal_service_token or x_internal_token != settings.internal_service_token:
        raise HTTPException(status_code=403, detail="Internal service authentication required")

    merchant = await repository.get_merchant_by_id(payload.merchant_id)
    if merchant is None:
        raise NotFoundError("Merchant not found")

    await repository.get_or_create_merchant_product(
        merchant_id=payload.merchant_id,
        brand_id=payload.brand_id,
        source_product_id=payload.source_product_id,
        title=payload.title,
        description=payload.description,
        source_url=str(payload.source_url),
    )
    garment, garment_created = await repository.get_or_create_garment(
        category=payload.category,
        subcategory=payload.subcategory,
        brand_id=payload.brand_id,
    )
    _, offer_created = await repository.create_or_update_offer(
        garment_id=garment.id,
        merchant_id=payload.merchant_id,
        source_product_id=payload.source_product_id,
        url=str(payload.source_url),
        price_minor=payload.price_minor,
        currency=payload.currency.upper(),
    )
    operation = "created" if garment_created or offer_created else "updated"
    return CatalogIntakeResponse(
        product_id=garment.id,
        operation=operation,
        enrichment_required=garment_created,
        ocr_required=garment_created,
    )
