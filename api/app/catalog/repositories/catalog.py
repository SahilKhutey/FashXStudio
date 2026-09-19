from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CanonicalGarment, Merchant, MerchantOffer, MerchantProduct


class CatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_garment(self, garment_id: UUID) -> CanonicalGarment | None:
        return await self.session.get(CanonicalGarment, garment_id)

    async def create_garment(self, *, category: str, subcategory: str | None = None, brand_id: UUID | None = None) -> CanonicalGarment:
        garment = CanonicalGarment(category=category, subcategory=subcategory, brand_id=brand_id)
        self.session.add(garment)
        await self.session.flush()
        return garment

    async def get_merchant_by_name(self, name: str) -> Merchant | None:
        statement = select(Merchant).where(Merchant.name == name)
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def get_merchant_product(self, merchant_id: UUID, source_product_id: str) -> MerchantProduct | None:
        statement = select(MerchantProduct).where(
            MerchantProduct.merchant_id == merchant_id,
            MerchantProduct.source_product_id == source_product_id,
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def create_merchant_product(self, *, merchant_id: UUID, brand_id: UUID | None, source_product_id: str, title: str, description: str | None, source_url: str) -> MerchantProduct:
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
        return item

    async def create_offer(
        self,
        *,
        garment_id: UUID,
        merchant_id: UUID,
        source_product_id: str,
        url: str,
        price_minor: int,
        currency: str = "INR",
    ) -> MerchantOffer:
        offer = MerchantOffer(
            garment_id=garment_id,
            merchant_id=merchant_id,
            source_product_id=source_product_id,
            url=url,
            price_minor=price_minor,
            currency=currency,
        )
        self.session.add(offer)
        await self.session.flush()
        return offer
