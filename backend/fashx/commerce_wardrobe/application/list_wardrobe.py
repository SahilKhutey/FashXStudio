from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
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
    image_url: str | None = None


class ListWardrobeUseCase:
    """Lists saved wardrobe items for a user with signed image URLs."""

    def __init__(
        self,
        uow: CommerceWardrobeUnitOfWork,
        storage: Any | None = None,
    ) -> None:
        self.uow = uow
        self.storage = storage

    def _resolve_image_url(self, key: str | None) -> str | None:
        if not key:
            return None
        if key.startswith("http://") or key.startswith("https://"):
            return key
        if self.storage and hasattr(self.storage, "signed_get_url"):
            try:
                return self.storage.signed_get_url(key, ttl_s=900)
            except Exception:
                return None
        return None

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
                    image_url=self._resolve_image_url(item.snapshot_image_key),
                )
                for item in items
            ]
