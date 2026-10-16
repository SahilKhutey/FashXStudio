from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from database.models.catalog import Brand
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.catalog.router import OfferDetail, get_catalog_uow
from fashx.core.errors import EntityNotFoundError
from fashx.security.deps import Principal, get_principal

customer_garment_router = APIRouter(tags=["customer-garments"])


class CustomerGarmentDetailResponse(BaseModel):
    id: UUID
    brand_id: UUID | None = None
    brand_name: str | None = None
    title: str
    category: str
    subcategory: str | None = None
    gender: str = "unisex"
    price_minor: int = 0
    currency: str = "INR"
    sizes_in_stock: list[str] = []
    tryon_supported: bool = True
    images: list[str] = []
    offers: list[OfferDetail] = []


async def _resolve_garment_detail(
    garment_id: UUID,
    uow: CatalogUnitOfWork,
) -> CustomerGarmentDetailResponse:
    async with uow:
        garment = await uow.canonical_garments.get_by_id(garment_id)
        if garment is None:
            raise EntityNotFoundError("CanonicalGarment", garment_id)

        brand_name: str | None = None
        if garment.brand_id:
            brand = await uow.session.get(Brand, garment.brand_id)
            if brand:
                brand_name = brand.name

        images_rec = await uow.images.list_for_garment(garment_id)
        images = [img.image_url for img in images_rec if img.image_url]

        offers = await uow.offers.list_for_garment(garment_id)
        currency = offers[0].currency if offers else "INR"
        price_minor = offers[0].price_minor if offers else garment.price_minor

        title = garment.display_name or f"{garment.category.capitalize()} {garment.subcategory or ''}".strip()

        return CustomerGarmentDetailResponse(
            id=garment.id,
            brand_id=garment.brand_id,
            brand_name=brand_name,
            title=title,
            category=garment.category,
            subcategory=garment.subcategory,
            gender=garment.gender,
            price_minor=price_minor,
            currency=currency,
            sizes_in_stock=garment.sizes_in_stock or [],
            tryon_supported=garment.tryon_supported,
            images=images,
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


@customer_garment_router.get(
    "/garments/{garment_id}",
    response_model=CustomerGarmentDetailResponse,
)
async def get_garment_detail(
    garment_id: UUID,
    principal: Principal = Depends(get_principal),
    uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> CustomerGarmentDetailResponse:
    """Customer-facing garment detail route (accessible without admin role)."""
    return await _resolve_garment_detail(garment_id, uow)


@customer_garment_router.get(
    "/catalog/garments/{garment_id}",
    response_model=CustomerGarmentDetailResponse,
)
async def get_catalog_garment_detail(
    garment_id: UUID,
    principal: Principal = Depends(get_principal),
    uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> CustomerGarmentDetailResponse:
    """Customer-facing alias under /catalog prefix (accessible without admin role)."""
    return await _resolve_garment_detail(garment_id, uow)
