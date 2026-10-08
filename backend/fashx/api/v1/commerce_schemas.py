from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from fashx.domain.commerce.enums import (
    BrandStatus,
    ListingStatus,
    MarketplaceStatus,
    SellerStatus,
    SellerType,
)


class BrandCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200)
    description: str | None = None
    website: str | None = None
    metadata: dict[str, str] = Field(
        default_factory=dict
    )


class SellerCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200)

    seller_type: SellerType = SellerType.RETAILER

    contact_email: str | None = None

    metadata: dict[str, str] = Field(
        default_factory=dict
    )


class MarketplaceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200)

    region: str | None = None
    website: str | None = None

    metadata: dict[str, str] = Field(
        default_factory=dict
    )


class BrandResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    status: BrandStatus
    website: str | None
    version: int


class SellerResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    seller_type: SellerType
    status: SellerStatus
    contact_email: str | None
    version: int


class MarketplaceResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: MarketplaceStatus
    region: str | None
    website: str | None
    version: int


class ProductBrandRequest(BaseModel):
    brand_id: UUID


class ProductBrandResponse(BaseModel):
    product_id: UUID
    brand_id: UUID


class ListingCreateRequest(BaseModel):
    product_id: UUID
    variant_id: UUID | None = None
    seller_id: UUID
    marketplace_id: UUID

    external_reference: str | None = None

    metadata: dict[str, str] = Field(
        default_factory=dict
    )


class ListingStatusRequest(BaseModel):
    status: ListingStatus


class ListingResponse(BaseModel):
    id: UUID
    product_id: UUID
    variant_id: UUID | None
    seller_id: UUID
    marketplace_id: UUID
    status: ListingStatus
    external_reference: str | None
    metadata: dict[str, str]
    version: int
