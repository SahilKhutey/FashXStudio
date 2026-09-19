from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth.dependencies import current_user_id
from api.app.catalog.application.catalog_use_cases import CatalogApplicationService
from api.app.catalog.repositories.catalog import CatalogRepository
from api.app.commerce.application import OfferSelectionService
from api.app.core.dependencies import object_storage
from api.app.core.dependencies import db_session
from api.app.core.errors import ConflictError
from api.app.core.errors import NotFoundError
from api.app.core.settings import get_settings
from schemas.catalog.detail import (
    CatalogDetail,
    CatalogImageView,
    CatalogOfferSelection,
    CatalogOfferView,
)
from schemas.catalog.enrichment import GarmentEnrichment
from schemas.catalog.garment import CanonicalGarment, MerchantOffer
from schemas.catalog.garment_image import GarmentImage
from schemas.catalog.intake import CatalogIntakeRequest, CatalogIntakeResponse
from schemas.catalog.search import CatalogItemSummary, CatalogSearchResponse

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


def get_repository(session: AsyncSession = Depends(db_session)) -> CatalogRepository:
    return CatalogRepository(session)


def get_application_service(repository: CatalogRepository = Depends(get_repository)) -> CatalogApplicationService:
    return CatalogApplicationService(repository)


def get_storage():
    try:
        return object_storage()
    except RuntimeError:
        return None


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
    rows = await repository.search_garments(
        category=category,
        subcategory=subcategory,
        price_min=price_min,
        price_max=price_max,
        limit=limit,
        cursor_id=cursor,
    )
    next_cursor = str(rows[-1][0].id) if len(rows) == limit else None
    return CatalogSearchResponse(
        products=[
            CatalogItemSummary(
                id=garment.id,
                display_name=garment.display_name,
                category=garment.category,
                subcategory=garment.subcategory,
                brand_id=garment.brand_id,
                version=garment.version,
                primary_image_key=primary_image,
                lowest_price_minor=lowest_price,
                currency="INR" if lowest_price is not None else None,
                in_stock=in_stock,
            )
            for garment, lowest_price, primary_image, in_stock in rows
        ],
        next_cursor=next_cursor,
    )


@router.get("/{product_id}", response_model=CatalogDetail)
async def get_catalog_item(
    product_id: UUID,
    offer_id: UUID | None = Query(default=None),
    _: UUID = Depends(current_user_id),
    repository: CatalogRepository = Depends(get_repository),
    storage=Depends(get_storage),
) -> CatalogDetail:
    garment = await repository.get_garment(product_id)
    if garment is None:
        raise NotFoundError("Catalog product not found")
    images = await repository.get_images(product_id)
    offers = await repository.get_offers(product_id)
    if offer_id is not None:
        selected = await repository.get_offer(product_id, offer_id)
        if selected is None or not selected.in_stock:
            raise NotFoundError("Selected merchant offer is unavailable")
    else:
        selected = next((offer for offer in offers if offer.in_stock), None)
    image_views = []
    for image in images:
        url = None
        if storage is not None:
            url, _ = storage.create_download_url(key=image.storage_key)
        image_views.append(
            CatalogImageView(
                id=str(image.id),
                image_type=image.image_type,
                url=url,
                version=image.version,
            )
        )
    offer_views = [
        CatalogOfferView(
            id=str(offer.id),
            merchant_id=str(offer.merchant_id),
            source_product_id=offer.source_product_id,
            url=offer.url,
            price_minor=offer.price_minor,
            currency=offer.currency,
            in_stock=offer.in_stock,
            selected=bool(selected and offer.id == selected.id),
        )
        for offer in offers
    ]
    enrichment = await repository.get_enrichment(product_id)
    return CatalogDetail(
        garment=CanonicalGarment.model_validate(garment, from_attributes=True),
        images=image_views,
        offers=offer_views,
        enrichment=GarmentEnrichment.model_validate(enrichment, from_attributes=True) if enrichment else None,
        selected_offer_id=str(selected.id) if selected else None,
    )


@router.post("/{product_id}/select-offer", response_model=CatalogDetail)
async def select_offer(
    product_id: UUID,
    payload: CatalogOfferSelection,
    user_id: UUID = Depends(current_user_id),
    repository: CatalogRepository = Depends(get_repository),
    storage=Depends(get_storage),
) -> CatalogDetail:
    try:
        selected_offer_id = UUID(payload.offer_id)
    except ValueError as exc:
        raise ConflictError("offer_id is invalid") from exc
    selected = await repository.get_offer(product_id, selected_offer_id)
    if selected is None or not selected.in_stock:
        raise NotFoundError("Selected merchant offer is unavailable")
    # Reuse the detail endpoint semantics without exposing a second data shape.
    return await get_catalog_item(product_id, selected_offer_id, user_id, repository, storage)


@router.post("/intake", response_model=CatalogIntakeResponse)
async def catalog_intake(
    payload: CatalogIntakeRequest,
    application: CatalogApplicationService = Depends(get_application_service),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> CatalogIntakeResponse:
    settings = get_settings()
    if not settings.internal_service_token or x_internal_token != settings.internal_service_token:
        raise HTTPException(status_code=403, detail="Internal service authentication required")
    try:
        return await application.intake_listing(payload)
    except ValueError as exc:
        raise NotFoundError(str(exc)) from exc
