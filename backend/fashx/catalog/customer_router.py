from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from database.models.catalog import Brand, Merchant
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.catalog.router import get_catalog_uow
from fashx.core.errors import EntityNotFoundError
from fashx.security.deps import Principal, get_principal

customer_garment_router = APIRouter(tags=["customer-garments"])


class CustomerOfferDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    merchant_id: UUID
    source_product_id: str
    url: str
    price_minor: int
    currency: str
    in_stock: bool
    updated_at: datetime | None = None
    merchant_name: str | None = None


class CustomerGarmentDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
    offers: list[CustomerOfferDetail] = []


async def _resolve_garment_detail(
    garment_id: UUID,
    uow: CatalogUnitOfWork,
) -> CustomerGarmentDetailResponse:
    async with uow:
        garment = await uow.canonical_garments.get_by_id(garment_id)
        if garment is None or not garment.active:
            raise EntityNotFoundError("CanonicalGarment", garment_id)

        brand_name: str | None = None
        if garment.brand_id:
            brand = await uow.session.get(Brand, garment.brand_id)
            if brand:
                brand_name = brand.name

        images_rec = await uow.images.list_for_garment(garment_id)
        images = [img.image_url for img in images_rec if img.image_url]

        offers = await uow.offers.list_for_garment(garment_id)

        # Collect merchant names
        merchant_ids = {o.merchant_id for o in offers}
        merchants_map: dict[UUID, str] = {}
        for m_id in merchant_ids:
            m = await uow.session.get(Merchant, m_id)
            if m:
                merchants_map[m_id] = m.name

        # Sort offers: in-stock first, then ascending by price
        sorted_offers = sorted(offers, key=lambda x: (not x.in_stock, x.price_minor))

        # Determine display price and currency: best in-stock, else best offer, else garment price
        in_stock_offers = [o for o in sorted_offers if o.in_stock]
        if in_stock_offers:
            best_offer = in_stock_offers[0]
            price_minor = best_offer.price_minor
            currency = best_offer.currency
        elif sorted_offers:
            best_offer = sorted_offers[0]
            price_minor = best_offer.price_minor
            currency = best_offer.currency
        else:
            price_minor = garment.price_minor
            currency = "INR"

        offers_detail = [
            CustomerOfferDetail(
                id=o.id,
                merchant_id=o.merchant_id,
                merchant_name=merchants_map.get(o.merchant_id),
                source_product_id=o.source_product_id,
                url=o.url,
                price_minor=o.price_minor,
                currency=o.currency,
                in_stock=o.in_stock,
                updated_at=getattr(o, "last_synced_at", None),
            )
            for o in sorted_offers
        ]

        title = (
            garment.display_name
            or f"{garment.category.capitalize()} {garment.subcategory or ''}".strip()
        )

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
            offers=offers_detail,
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
