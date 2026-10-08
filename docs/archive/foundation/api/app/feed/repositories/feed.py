from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CanonicalGarment, GarmentImage, MerchantOffer
from database.models.commerce_feedback import FeedExclusion


class FeedRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_items(
        self,
        *,
        user_id: UUID,
        category: str | None,
        subcategory: str | None,
        price_min: int | None,
        price_max: int | None,
        limit: int,
        cursor: tuple[datetime, UUID] | None,
    ) -> list[tuple[CanonicalGarment, int | None, str | None, bool]]:
        min_price = func.min(MerchantOffer.price_minor).label("lowest_price_minor")
        primary_image = (
            select(GarmentImage.storage_key)
            .where(
                GarmentImage.garment_id == CanonicalGarment.id,
                GarmentImage.image_type.in_(["front", "model"]),
            )
            .order_by(GarmentImage.version.asc(), GarmentImage.id.asc())
            .limit(1)
            .scalar_subquery()
        )
        available_stock = func.bool_or(MerchantOffer.in_stock).label("in_stock")
        statement = (
            select(CanonicalGarment, min_price, primary_image.label("primary_image_key"), available_stock)
            .join(MerchantOffer, MerchantOffer.garment_id == CanonicalGarment.id)
            .where(MerchantOffer.in_stock.is_(True))
            .where(~select(FeedExclusion.garment_id).where(
                FeedExclusion.user_id == user_id,
                FeedExclusion.garment_id == CanonicalGarment.id,
            ).exists())
            .group_by(CanonicalGarment.id)
            .order_by(CanonicalGarment.created_at.desc(), CanonicalGarment.id.desc())
            .limit(limit)
        )
        if category:
            statement = statement.where(CanonicalGarment.category == category)
        if subcategory:
            statement = statement.where(CanonicalGarment.subcategory == subcategory)
        if cursor:
            created_at, garment_id = cursor
            statement = statement.where(
                or_(
                    CanonicalGarment.created_at < created_at,
                    and_(CanonicalGarment.created_at == created_at, CanonicalGarment.id < garment_id),
                )
            )
        if price_min is not None:
            statement = statement.where(MerchantOffer.price_minor >= price_min)
        if price_max is not None:
            statement = statement.where(MerchantOffer.price_minor <= price_max)

        rows = (await self.session.execute(statement)).all()
        return [(row[0], row[1], row[2], bool(row[3])) for row in rows]

    async def get_created_at(self, garment_id: UUID) -> datetime | None:
        statement = select(CanonicalGarment.created_at).where(CanonicalGarment.id == garment_id)
        return (await self.session.execute(statement)).scalar_one_or_none()
