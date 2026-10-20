from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from fashx.core.errors import EntityNotFoundError


@dataclass(frozen=True)
class MarkPurchasedCommand:
    user_id: UUID
    item_id: UUID
    purchased: bool = True


@dataclass(frozen=True)
class MarkPurchasedResult:
    item_id: UUID
    purchased_at: datetime | None


class MarkPurchasedUseCase:
    """Marks a wardrobe item as purchased, scoped to owner (idempotent)."""

    def __init__(self, uow: CommerceWardrobeUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, cmd: MarkPurchasedCommand) -> MarkPurchasedResult:
        async with self.uow:
            item = await self.uow.wardrobe.get_by_id_and_user(cmd.item_id, cmd.user_id)
            if item is None:
                raise EntityNotFoundError("WardrobeItem", cmd.item_id)

            if cmd.purchased and item.purchased_at is None:
                item.purchased_at = datetime.now(UTC)
                await self.uow.commit()

            return MarkPurchasedResult(
                item_id=item.id,
                purchased_at=item.purchased_at,
            )
