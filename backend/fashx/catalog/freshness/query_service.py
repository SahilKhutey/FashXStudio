"""High-performance catalog query and discovery service supporting multi-factor filters."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.catalog import (
    Brand,
    CanonicalGarment,
    GarmentImage,
    MerchantOffer,
    MerchantProduct,
)
from database.models.catalog_freshness import (
    MerchantOfferSize,
    OfferPriceHistory,
    ProductVariant,
)


@dataclass
class CatalogFilterParams:
    category: str | None = None
    subcategory: str | None = None
    brand_id: UUID | None = None
    brand_name: str | None = None
    min_price: int | None = None
    max_price: int | None = None
    currency: str = "INR"
    in_stock_only: bool = True
    size: str | None = None
    color: str | None = None
    merchant_id: UUID | None = None
    source_id: UUID | None = None
    limit: int = 50
    offset: int = 0


@dataclass
class ProductDetailResult:
    garment: CanonicalGarment
    brand: Brand | None
    offers: list[MerchantOffer]
    images: list[GarmentImage]
    variants: list[ProductVariant]


class CatalogQueryService:
    """Provides efficient, indexed queries for catalog discovery and merchant administrative tooling."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def lookup_by_source_identity(
        self, source_id: UUID, source_product_id: str
    ) -> MerchantProduct | None:
        """Fast lookup by source identity leveraging uq_product_source_pid unique index."""
        stmt = (
            select(MerchantProduct)
            .where(
                MerchantProduct.source_id == source_id,
                MerchantProduct.source_product_id == source_product_id,
            )
            .options(selectinload(MerchantProduct.offers))
        )
        return (await self.session.scalars(stmt)).first()

    async def get_garment_detail(self, garment_id: UUID) -> ProductDetailResult | None:
        """Fetch canonical garment details with active offers, brand, images, and variants."""
        stmt = select(CanonicalGarment).where(CanonicalGarment.id == garment_id)
        garment = (await self.session.scalars(stmt)).first()
        if garment is None:
            return None

        # Fetch Brand
        brand = None
        if garment.brand_id:
            brand_stmt = select(Brand).where(Brand.id == garment.brand_id)
            brand = (await self.session.scalars(brand_stmt)).first()

        # Fetch Offers
        offers_stmt = (
            select(MerchantOffer)
            .where(
                MerchantOffer.garment_id == garment_id,
                MerchantOffer.status == "ACTIVE",
            )
            .order_by(MerchantOffer.price_minor.asc())
        )
        offers = list((await self.session.scalars(offers_stmt)).all())

        # Fetch Images
        images_stmt = select(GarmentImage).where(GarmentImage.garment_id == garment_id)
        images = list((await self.session.scalars(images_stmt)).all())

        # Fetch Variants
        variants_stmt = select(ProductVariant).where(
            ProductVariant.canonical_garment_id == garment_id
        )
        variants = list((await self.session.scalars(variants_stmt)).all())

        return ProductDetailResult(
            garment=garment,
            brand=brand,
            offers=offers,
            images=images,
            variants=variants,
        )

    async def search_catalog(self, params: CatalogFilterParams) -> list[CanonicalGarment]:
        """Multi-factor search supporting category, brand, price range, size, color, and stock."""
        stmt = (
            select(CanonicalGarment)
            .join(MerchantOffer, MerchantOffer.garment_id == CanonicalGarment.id)
            .where(CanonicalGarment.active.is_(True))
        )

        if params.in_stock_only:
            stmt = stmt.where(
                CanonicalGarment.in_stock.is_(True),
                MerchantOffer.in_stock.is_(True),
                MerchantOffer.status == "ACTIVE",
            )

        if params.category:
            stmt = stmt.where(CanonicalGarment.category == params.category)
        if params.subcategory:
            stmt = stmt.where(CanonicalGarment.subcategory == params.subcategory)

        if params.brand_id:
            stmt = stmt.where(CanonicalGarment.brand_id == params.brand_id)
        elif params.brand_name:
            stmt = stmt.join(Brand, Brand.id == CanonicalGarment.brand_id).where(
                Brand.name.ilike(f"%{params.brand_name}%")
            )

        if params.currency:
            stmt = stmt.where(MerchantOffer.currency == params.currency)

        if params.min_price is not None:
            stmt = stmt.where(MerchantOffer.price_minor >= params.min_price)
        if params.max_price is not None:
            stmt = stmt.where(MerchantOffer.price_minor <= params.max_price)

        if params.merchant_id:
            stmt = stmt.where(MerchantOffer.merchant_id == params.merchant_id)

        if params.color:
            stmt = stmt.where(CanonicalGarment.color_family == params.color)

        if params.size:
            # Join through merchant offer sizes or sizes_in_stock
            stmt = stmt.join(
                MerchantOfferSize,
                MerchantOfferSize.merchant_offer_id == MerchantOffer.id,
            ).where(
                MerchantOfferSize.raw_size.ilike(params.size),
                MerchantOfferSize.availability == "IN_STOCK",
            )

        stmt = (
            stmt.distinct()
            .order_by(MerchantOffer.price_minor.asc())
            .limit(params.limit)
            .offset(params.offset)
        )

        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_price_history(self, offer_id: UUID, limit: int = 50) -> list[OfferPriceHistory]:
        """Fetch historical price observations for a merchant offer."""
        stmt = (
            select(OfferPriceHistory)
            .where(OfferPriceHistory.merchant_offer_id == offer_id)
            .order_by(OfferPriceHistory.observed_at.desc())
            .limit(limit)
        )
        return list((await self.session.scalars(stmt)).all())

    async def list_merchant_active_offers(
        self, merchant_id: UUID, limit: int = 100
    ) -> Sequence[MerchantOffer]:
        """List active offers belonging to a specific merchant."""
        stmt = (
            select(MerchantOffer)
            .where(
                MerchantOffer.merchant_id == merchant_id,
                MerchantOffer.status == "ACTIVE",
            )
            .order_by(MerchantOffer.updated_at.desc())
            .limit(limit)
        )
        return (await self.session.scalars(stmt)).all()
