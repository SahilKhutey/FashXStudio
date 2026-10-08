from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.bootstrap import register_core_services
from app.core.context import CoreContext
from app.core.runtime import get_core_runtime
from fashx.domain.commerce.entities import (
    Brand,
    Marketplace,
    MarketplaceListing,
    Seller,
)
from fashx.domain.commerce.service import CommerceService

from .commerce_schemas import (
    BrandCreateRequest,
    BrandResponse,
    ListingCreateRequest,
    ListingResponse,
    ListingStatusRequest,
    MarketplaceCreateRequest,
    MarketplaceResponse,
    ProductBrandRequest,
    ProductBrandResponse,
    SellerCreateRequest,
    SellerResponse,
)

router = APIRouter(
    prefix="/commerce",
    tags=["commerce"],
)


def get_commerce_service() -> CommerceService:
    register_core_services()
    return get_core_runtime().registry.get(
        "commerce_service"
    )


@router.post(
    "/brands",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_brand(
    payload: BrandCreateRequest,
    service: CommerceService = Depends(
        get_commerce_service
    ),
):

    return await service.create_brand(
        context=CoreContext.create(),
        brand=Brand(
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            website=payload.website,
            metadata=payload.metadata,
        ),
    )


@router.post(
    "/sellers",
    response_model=SellerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_seller(
    payload: SellerCreateRequest,
    service: CommerceService = Depends(
        get_commerce_service
    ),
):

    return await service.create_seller(
        context=CoreContext.create(),
        seller=Seller(
            name=payload.name,
            slug=payload.slug,
            seller_type=payload.seller_type,
            contact_email=payload.contact_email,
            metadata=payload.metadata,
        ),
    )


@router.post(
    "/marketplaces",
    response_model=MarketplaceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_marketplace(
    payload: MarketplaceCreateRequest,
    service: CommerceService = Depends(
        get_commerce_service
    ),
):

    return await service.create_marketplace(
        context=CoreContext.create(),
        marketplace=Marketplace(
            name=payload.name,
            slug=payload.slug,
            region=payload.region,
            website=payload.website,
            metadata=payload.metadata,
        ),
    )


@router.put(
    "/products/{product_id}/brand",
    response_model=ProductBrandResponse,
)
async def assign_product_brand(
    product_id: UUID,
    payload: ProductBrandRequest,
    service: CommerceService = Depends(
        get_commerce_service
    ),
):

    return await service.assign_product_brand(
        context=CoreContext.create(),
        product_id=product_id,
        brand_id=payload.brand_id,
    )


@router.get(
    "/products/{product_id}/brand",
    response_model=ProductBrandResponse,
)
async def get_product_brand(
    product_id: UUID,
    service: CommerceService = Depends(
        get_commerce_service
    ),
):

    return await service.get_product_brand(
        product_id
    )


@router.post(
    "/listings",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_listing(
    payload: ListingCreateRequest,
    service: CommerceService = Depends(
        get_commerce_service
    ),
):

    listing = MarketplaceListing(
        product_id=payload.product_id,
        variant_id=payload.variant_id,
        seller_id=payload.seller_id,
        marketplace_id=payload.marketplace_id,
        external_reference=payload.external_reference,
        metadata=payload.metadata,
    )

    return await service.create_listing(
        context=CoreContext.create(),
        listing=listing,
    )


@router.get(
    "/listings/{listing_id}",
    response_model=ListingResponse,
)
async def get_listing(
    listing_id: UUID,
    service: CommerceService = Depends(
        get_commerce_service
    ),
):

    return await service.get_listing(listing_id)


@router.get(
    "/products/{product_id}/listings",
    response_model=list[ListingResponse],
)
async def product_listings(
    product_id: UUID,
    service: CommerceService = Depends(
        get_commerce_service
    ),
):

    return await service.list_product_listings(
        product_id
    )


@router.get(
    "/sellers/{seller_id}/listings",
    response_model=list[ListingResponse],
)
async def seller_listings(
    seller_id: UUID,
    service: CommerceService = Depends(
        get_commerce_service
    ),
):

    return await service.list_seller_listings(
        seller_id
    )


@router.post(
    "/listings/{listing_id}/status",
    response_model=ListingResponse,
)
async def change_listing_status(
    listing_id: UUID,
    payload: ListingStatusRequest,
    service: CommerceService = Depends(
        get_commerce_service
    ),
):

    return await service.change_listing_status(
        context=CoreContext.create(),
        listing_id=listing_id,
        target=payload.status,
    )
