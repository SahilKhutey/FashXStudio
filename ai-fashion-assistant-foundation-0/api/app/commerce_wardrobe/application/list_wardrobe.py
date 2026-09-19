from dataclasses import dataclass
from uuid import UUID

from api.app.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)


@dataclass(frozen=True)
class WardrobeItemView:
    item_id: UUID
    user_id: UUID
    garment_id: UUID
    snapshot_title: str
    snapshot_price_minor: int
    snapshot_currency: str
    snapshot_image_key: str
    tryon_artifact_id: UUID | None
    saved_at: str


class ListWardrobeUseCase:
    """Lists saved wardrobe items for a user."""

    def __init__(self, uow: CommerceWardrobeUnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[WardrobeItemView]:
        async with self.uow:
            items = await self.uow.wardrobe.list_for_user(user_id, limit=limit, offset=offset)
            return [
                WardrobeItemView(
                    item_id=item.id,
                    user_id=item.user_id,
                    garment_id=item.garment_id,
                    snapshot_title=item.snapshot_title,
                    snapshot_price_minor=item.snapshot_price_minor,
                    snapshot_currency=item.snapshot_currency,
                    snapshot_image_key=item.snapshot_image_key,
                    tryon_artifact_id=item.tryon_artifact_id,
                    saved_at=item.saved_at.isoformat() if item.saved_at else "",
                )
                for item in items
            ]
