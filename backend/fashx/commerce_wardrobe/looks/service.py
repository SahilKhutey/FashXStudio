from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from fashx.commerce_wardrobe.looks.schemas import (
    CreateSavedLookRequest,
    SavedLookSummary,
)


class LookOwnershipError(PermissionError):
    """Raised when one or more wardrobe items do not belong to the authenticated user."""


class LookValidationError(ValueError):
    """Raised when saved look input violates domain constraints."""


class SavedLookRepositoryProtocol(Protocol):
    async def get_owned_item_ids(
        self, user_id: UUID, item_ids: list[UUID]
    ) -> set[UUID]: ...

    async def persist_look(self, look: SavedLookSummary) -> SavedLookSummary: ...

    async def get_look(
        self, user_id: UUID, look_id: UUID
    ) -> SavedLookSummary | None: ...

    async def list_looks(self, user_id: UUID) -> list[SavedLookSummary]: ...

    async def delete_look(self, user_id: UUID, look_id: UUID) -> bool: ...


async def create_saved_look_for_user(
    repository: SavedLookRepositoryProtocol,
    user_id: UUID,
    payload: CreateSavedLookRequest,
) -> SavedLookSummary:
    """Create a saved look atomically only if every referenced item belongs to user_id."""
    deduped_ids = list(dict.fromkeys(payload.item_ids))
    if not deduped_ids:
        raise LookValidationError("LOOK_REQUIRES_AT_LEAST_ONE_ITEM")

    owned_ids = await repository.get_owned_item_ids(user_id=user_id, item_ids=deduped_ids)
    if len(owned_ids) != len(deduped_ids):
        raise LookOwnershipError("LOOK_CONTAINS_UNAVAILABLE_ITEMS")

    now = datetime.now(UTC)
    look = SavedLookSummary(
        id=uuid4(),
        user_id=user_id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        item_ids=deduped_ids,
        item_count=len(deduped_ids),
        created_at=now,
        updated_at=now,
    )
    return await repository.persist_look(look)
