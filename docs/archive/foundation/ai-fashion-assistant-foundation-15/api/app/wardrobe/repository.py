from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.commerce_feedback import FeedExclusion, WardrobeItem


class WardrobeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_saved(self, user_id: UUID, garment_id: UUID) -> WardrobeItem | None:
        statement = select(WardrobeItem).where(
            WardrobeItem.user_id == user_id,
            WardrobeItem.garment_id == garment_id,
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def save_item(
        self,
        *,
        user_id: UUID,
        garment_id: UUID,
        offer_id: UUID | None,
        snapshot_title: str,
        snapshot_price_minor: int,
        snapshot_currency: str,
        snapshot_image_key: str,
        tryon_artifact_id: UUID | None = None,
    ) -> tuple[WardrobeItem, bool]:
        existing = await self.get_saved(user_id, garment_id)
        if existing:
            return existing, False
        item = WardrobeItem(
            user_id=user_id,
            garment_id=garment_id,
            offer_id=offer_id,
            snapshot_title=snapshot_title,
            snapshot_price_minor=snapshot_price_minor,
            snapshot_currency=snapshot_currency,
            snapshot_image_key=snapshot_image_key,
            tryon_artifact_id=tryon_artifact_id,
        )
        self.session.add(item)
        await self.session.flush()
        return item, True

    async def reject(self, user_id: UUID, garment_id: UUID, reason: str = "rejected") -> None:
        statement = select(FeedExclusion).where(
            FeedExclusion.user_id == user_id,
            FeedExclusion.garment_id == garment_id,
        )
        existing = (await self.session.execute(statement)).scalar_one_or_none()
        if existing:
            return
        self.session.add(FeedExclusion(user_id=user_id, garment_id=garment_id, reason=reason))
        await self.session.flush()
