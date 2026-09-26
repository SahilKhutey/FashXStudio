from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from app.core.contracts import Entity
from app.core.errors import ValidationError
from app.core.ids import new_id

from .enums import (
    BrandStatus,
    ListingStatus,
    MarketplaceStatus,
    SellerStatus,
    SellerType,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Brand(Entity):
    id: UUID = field(default_factory=new_id)

    name: str = ""
    slug: str = ""

    description: str | None = None

    status: BrandStatus = BrandStatus.DRAFT

    website: str | None = None

    metadata: dict[str, str] = field(
        default_factory=dict
    )

    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    version: int = 1

    def validate(self) -> None:
        if not self.name.strip():
            raise ValidationError(
                "Brand name cannot be empty.",
                {"field": "name"},
            )

        if not self.slug.strip():
            raise ValidationError(
                "Brand slug cannot be empty.",
                {"field": "slug"},
            )

        if len(self.name) > 200:
            raise ValidationError(
                "Brand name cannot exceed 200 characters.",
                {"field": "name"},
            )

        if len(self.slug) > 200:
            raise ValidationError(
                "Brand slug cannot exceed 200 characters.",
                {"field": "slug"},
            )

        if self.version < 1:
            raise ValidationError(
                "Brand version must be positive."
            )

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1


@dataclass(slots=True)
class Seller(Entity):
    id: UUID = field(default_factory=new_id)

    name: str = ""
    slug: str = ""

    seller_type: SellerType = SellerType.RETAILER

    status: SellerStatus = SellerStatus.PENDING

    contact_email: str | None = None

    metadata: dict[str, str] = field(
        default_factory=dict
    )

    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    version: int = 1

    def validate(self) -> None:
        if not self.name.strip():
            raise ValidationError(
                "Seller name cannot be empty.",
                {"field": "name"},
            )

        if not self.slug.strip():
            raise ValidationError(
                "Seller slug cannot be empty.",
                {"field": "slug"},
            )

        if len(self.name) > 200:
            raise ValidationError(
                "Seller name cannot exceed 200 characters.",
                {"field": "name"},
            )

        if len(self.slug) > 200:
            raise ValidationError(
                "Seller slug cannot exceed 200 characters.",
                {"field": "slug"},
            )

        if self.version < 1:
            raise ValidationError(
                "Seller version must be positive."
            )

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1


@dataclass(slots=True)
class Marketplace(Entity):
    id: UUID = field(default_factory=new_id)

    name: str = ""
    slug: str = ""

    status: MarketplaceStatus = (
        MarketplaceStatus.DRAFT
    )

    region: str | None = None

    website: str | None = None

    metadata: dict[str, str] = field(
        default_factory=dict
    )

    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    version: int = 1

    def validate(self) -> None:
        if not self.name.strip():
            raise ValidationError(
                "Marketplace name cannot be empty.",
                {"field": "name"},
            )

        if not self.slug.strip():
            raise ValidationError(
                "Marketplace slug cannot be empty.",
                {"field": "slug"},
            )

        if len(self.name) > 200:
            raise ValidationError(
                "Marketplace name cannot exceed 200 characters.",
                {"field": "name"},
            )

        if len(self.slug) > 200:
            raise ValidationError(
                "Marketplace slug cannot exceed 200 characters.",
                {"field": "slug"},
            )

        if self.version < 1:
            raise ValidationError(
                "Marketplace version must be positive."
            )

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1


@dataclass(slots=True)
class ProductBrand:
    product_id: UUID
    brand_id: UUID

    created_at: datetime = field(
        default_factory=utc_now
    )

    def validate(self) -> None:
        if self.product_id == self.brand_id:
            raise ValidationError(
                "Product ID and brand ID cannot be identical."
            )


@dataclass(slots=True)
class MarketplaceListing(Entity):
    id: UUID = field(default_factory=new_id)

    product_id: UUID | None = None

    variant_id: UUID | None = None

    seller_id: UUID | None = None

    marketplace_id: UUID | None = None

    status: ListingStatus = ListingStatus.DRAFT

    external_reference: str | None = None

    metadata: dict[str, str] = field(
        default_factory=dict
    )

    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    version: int = 1

    def validate(self) -> None:
        if self.product_id is None:
            raise ValidationError(
                "Product ID is required."
            )

        if self.seller_id is None:
            raise ValidationError(
                "Seller ID is required."
            )

        if self.marketplace_id is None:
            raise ValidationError(
                "Marketplace ID is required."
            )

        if self.version < 1:
            raise ValidationError(
                "Listing version must be positive."
            )

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1
