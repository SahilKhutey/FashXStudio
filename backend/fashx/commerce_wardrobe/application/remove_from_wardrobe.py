from uuid import UUID

from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from api.app.core.errors import EntityNotFoundError


class RemoveFromWardrobeUseCase:
    """Removes an item from the user's virtual closet."""

    def __init__(self, uow: CommerceWardrobeUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, user_id: UUID, item_id: UUID) -> bool:
        async with self.uow:
            item = await self.uow.wardrobe.get_by_id(item_id)
            if item is None or item.user_id != user_id:
                raise EntityNotFoundError("WardrobeItem", item_id)

            await self.uow.wardrobe.delete(item)
            await self.uow.commit()
            return True
