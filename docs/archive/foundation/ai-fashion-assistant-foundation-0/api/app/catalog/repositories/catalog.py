from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import (
    Brand,
    CanonicalGarment,
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
        self, *, category: str, subcategory: str | None = None, brand_id: UUID | None = None
    ) -> CanonicalGarment:
        garment = CanonicalGarment(category=category, subcategory=subcategory, brand_id=brand_id)
        self.session.add(garment)
        await self.session.flush()
        return garment

    async def get_merchant_by_id(self, merchant_id: UUID) -> Merchant | None:
        return await self.session.get(Merchant, merchant_id)

    async def get_or_create_merchant_product(
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

    async def get_or_create_garment(
        self, *, category: str, subcategory: str | None, brand_id: UUID | None
    ) -> tuple[CanonicalGarment, bool]:
        statement = select(CanonicalGarment).where(
            CanonicalGarment.category == category,
            CanonicalGarment.subcategory == subcategory,
            CanonicalGarment.brand_id == brand_id,
        ).limit(1)
        garment = (await self.session.execute(statement)).scalar_one_or_none()
        if garment:
            return garment, False
        garment = CanonicalGarment(category=category, subcategory=subcategory, brand_id=brand_id)
        self.session.add(garment)
        await self.session.flush()
        return garment, True

    async def get_offer(
        self, *, garment_id: UUID, merchant_id: UUID, source_product_id: str
    ) -> MerchantOffer | None:
        statement = select(MerchantOffer).where(
            MerchantOffer.garment_id == garment_id,
            MerchantOffer.merchant_id == merchant_id,
            MerchantOffer.source_product_id == source_product_id,
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def create_or_update_offer(
        self,
        *,
        garment_id: UUID,
        merchant_id: UUID,
        source_product_id: str,
        url: str,
        price_minor: int,
        currency: str,
    ) -> tuple[MerchantOffer, bool]:
        offer = await self.get_offer(
            garment_id=garment_id,
            merchant_id=merchant_id,
            source_product_id=source_product_id,
        )
        if offer:
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

    async def search_garments(
        self,
        *,
        category: str | None,
        subcategory: str | None,
        price_min: int | None,
        price_max: int | None,
        limit: int,
        cursor_id: UUID | None = None,
    ) -> list[CanonicalGarment]:
        statement = select(CanonicalGarment).order_by(CanonicalGarment.id).limit(limit)
        if category:
            statement = statement.where(CanonicalGarment.category == category)
        if subcategory:
            statement = statement.where(CanonicalGarment.subcategory == subcategory)
        if cursor_id:
            statement = statement.where(CanonicalGarment.id > cursor_id)
        if price_min is not None or price_max is not None:
            statement = statement.join(MerchantOffer, MerchantOffer.garment_id == CanonicalGarment.id)
            if price_min is not None:
                statement = statement.where(MerchantOffer.price_minor >= price_min)
            if price_max is not None:
                statement = statement.where(MerchantOffer.price_minor <= price_max)
            statement = statement.distinct()
        return list((await self.session.execute(statement)).scalars().all())

    async def get_images(self, garment_id: UUID) -> list[GarmentImage]:
        statement = select(GarmentImage).where(GarmentImage.garment_id == garment_id).order_by(GarmentImage.version.desc())
        return list((await self.session.execute(statement)).scalars().all())

    async def get_offers(self, garment_id: UUID) -> list[MerchantOffer]:
        statement = select(MerchantOffer).where(MerchantOffer.garment_id == garment_id).order_by(MerchantOffer.last_synced_at.desc())
        return list((await self.session.execute(statement)).scalars().all())
