from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import (
    Brand,
    CanonicalGarment,
    GarmentEnrichment,
    GarmentImage,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)


class CatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_garment(self, garment_id: UUID) -> CanonicalGarment | None:
        return await self.session.get(CanonicalGarment, garment_id)

    async def create_garment(
        self,
        *,
        display_name: str,
        category: str,
        subcategory: str | None = None,
        brand_id: UUID | None = None,
    ) -> CanonicalGarment:
        garment = CanonicalGarment(
            display_name=display_name,
            category=category,
            subcategory=subcategory,
            brand_id=brand_id,
        )
        self.session.add(garment)
        await self.session.flush()
        return garment

    async def update_garment(
        self,
        garment: CanonicalGarment,
        *,
        display_name: str,
        category: str,
        subcategory: str | None,
        brand_id: UUID | None,
    ) -> CanonicalGarment:
        changed = (
            garment.display_name != display_name
            or garment.category != category
            or garment.subcategory != subcategory
            or garment.brand_id != brand_id
        )
        garment.display_name = display_name
        garment.category = category
        garment.subcategory = subcategory
        garment.brand_id = brand_id
        if changed:
            garment.version += 1
        await self.session.flush()
        return garment

    async def get_merchant_by_id(self, merchant_id: UUID) -> Merchant | None:
        return await self.session.get(Merchant, merchant_id)

    async def get_merchant_by_name(self, normalized_name: str) -> Merchant | None:
        statement = select(Merchant).where(func.lower(Merchant.name) == normalized_name.lower())
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def get_or_create_brand(self, *, name: str) -> tuple[Brand, bool]:
        normalized = " ".join(name.strip().lower().split())
        statement = select(Brand).where(Brand.normalized_name == normalized)
        brand = (await self.session.execute(statement)).scalar_one_or_none()
        if brand:
            return brand, False
        brand = Brand(name=name.strip(), normalized_name=normalized)
        self.session.add(brand)
        await self.session.flush()
        return brand, True

    async def get_or_create_merchant(self, *, name: str, merchant_type: str) -> tuple[Merchant, bool]:
        normalized = " ".join(name.strip().lower().split())
        statement = select(Merchant).where(func.lower(Merchant.name) == normalized)
        merchant = (await self.session.execute(statement)).scalar_one_or_none()
        if merchant:
            return merchant, False
        merchant = Merchant(name=name.strip(), merchant_type=merchant_type)
        self.session.add(merchant)
        await self.session.flush()
        return merchant, True

    async def upsert_merchant_product(
        self,
        *,
        merchant_id: UUID,
        brand_id: UUID | None,
        source_product_id: str,
        title: str,
        description: str | None,
        source_url: str,
    ) -> tuple[MerchantProduct, bool]:
        statement = select(MerchantProduct).where(
            MerchantProduct.merchant_id == merchant_id,
            MerchantProduct.source_product_id == source_product_id,
        )
        item = (await self.session.execute(statement)).scalar_one_or_none()
        if item:
            item.title = title
            item.description = description
            item.source_url = source_url
            item.brand_id = brand_id
            await self.session.flush()
            return item, False
        item = MerchantProduct(
            merchant_id=merchant_id,
            brand_id=brand_id,
            source_product_id=source_product_id,
            title=title,
            description=description,
            source_url=source_url,
        )
        self.session.add(item)
        await self.session.flush()
        return item, True

    async def upsert_offer(
        self,
        *,
        garment_id: UUID,
        merchant_id: UUID,
        source_product_id: str,
        url: str,
        price_minor: int,
        currency: str,
    ) -> tuple[MerchantOffer, bool]:
        statement = select(MerchantOffer).where(
            MerchantOffer.merchant_id == merchant_id,
            MerchantOffer.source_product_id == source_product_id,
        )
        offer = (await self.session.execute(statement)).scalar_one_or_none()
        if offer:
            offer.garment_id = garment_id
            offer.url = url
            offer.price_minor = price_minor
            offer.currency = currency
            offer.in_stock = True
            await self.session.flush()
            return offer, False
        offer = MerchantOffer(
            garment_id=garment_id,
            merchant_id=merchant_id,
            source_product_id=source_product_id,
            url=url,
            price_minor=price_minor,
            currency=currency,
            in_stock=True,
        )
        self.session.add(offer)
        await self.session.flush()
        return offer, True

    async def upsert_image(
        self,
        *,
        garment_id: UUID,
        storage_key: str,
        content_hash: str,
        perceptual_hash: str | None,
        image_type: str,
    ) -> tuple[GarmentImage, bool]:
        statement = select(GarmentImage).where(
            GarmentImage.garment_id == garment_id,
            GarmentImage.content_hash == content_hash,
        )
        image = (await self.session.execute(statement)).scalar_one_or_none()
        if image:
            image.storage_key = storage_key
            image.perceptual_hash = perceptual_hash
            image.image_type = image_type
            await self.session.flush()
            return image, False
        image = GarmentImage(
            garment_id=garment_id,
            storage_key=storage_key,
            content_hash=content_hash,
            perceptual_hash=perceptual_hash,
            image_type=image_type,
        )
        self.session.add(image)
        await self.session.flush()
        return image, True

    async def search_garments(
        self,
        *,
        category: str | None,
        subcategory: str | None,
        price_min: int | None,
        price_max: int | None,
        limit: int,
        cursor_id: UUID | None = None,
    ) -> list[tuple[CanonicalGarment, int | None, str | None, bool]]:
        min_price = func.min(MerchantOffer.price_minor).label("lowest_price_minor")
        primary_image = (
            select(GarmentImage.storage_key)
            .where(
                GarmentImage.garment_id == CanonicalGarment.id,
                GarmentImage.image_type.in_(["front", "model"]),
            )
            .order_by(GarmentImage.version.asc())
            .limit(1)
            .scalar_subquery()
        )
        in_stock = func.bool_or(MerchantOffer.in_stock).label("in_stock")
        statement = (
            select(CanonicalGarment, min_price, primary_image.label("primary_image_key"), in_stock)
            .join(MerchantOffer, MerchantOffer.garment_id == CanonicalGarment.id)
            .where(MerchantOffer.in_stock.is_(True))
            .group_by(CanonicalGarment.id)
            .order_by(CanonicalGarment.id)
            .limit(limit)
        )
        if category:
            statement = statement.where(CanonicalGarment.category == category)
        if subcategory:
            statement = statement.where(CanonicalGarment.subcategory == subcategory)
        if cursor_id:
            statement = statement.where(CanonicalGarment.id > cursor_id)
        if price_min is not None:
            statement = statement.where(MerchantOffer.price_minor >= price_min)
        if price_max is not None:
            statement = statement.where(MerchantOffer.price_minor <= price_max)
        rows = (await self.session.execute(statement)).all()
        return [(row[0], row[1], row[2], bool(row[3])) for row in rows]

    async def get_images(self, garment_id: UUID) -> list[GarmentImage]:
        statement = select(GarmentImage).where(GarmentImage.garment_id == garment_id).order_by(GarmentImage.version.asc())
        return list((await self.session.execute(statement)).scalars().all())

    async def get_offers(self, garment_id: UUID) -> list[MerchantOffer]:
        statement = select(MerchantOffer).where(MerchantOffer.garment_id == garment_id).order_by(MerchantOffer.last_synced_at.desc())
        return list((await self.session.execute(statement)).scalars().all())

    async def get_enrichment(self, garment_id: UUID) -> GarmentEnrichment | None:
        statement = (
            select(GarmentEnrichment)
            .where(GarmentEnrichment.garment_id == garment_id)
            .order_by(GarmentEnrichment.created_at.desc())
            .limit(1)
        )
        return (await self.session.execute(statement)).scalar_one_or_none()
