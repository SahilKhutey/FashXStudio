from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from fashx.commerce_wardrobe.looks.schemas import (
    CreateSavedLookRequest,
    SavedLookSummary,
    SaveWardrobeItemRequest,
    WardrobeItemType,
)
from fashx.commerce_wardrobe.looks.service import (
    LookOwnershipError,
    create_saved_look_for_user,
)


def _run(coro):
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise RuntimeError("Unexpected async suspension in unit test")


class _InMemoryLookRepo:
    def __init__(self, owned_by_user: dict[UUID, set[UUID]]) -> None:
        self.owned_by_user = owned_by_user
        self.looks: dict[UUID, SavedLookSummary] = {}

    async def get_owned_item_ids(
        self, user_id: UUID, item_ids: list[UUID]
    ) -> set[UUID]:
        owned = self.owned_by_user.get(user_id, set())
        return {item_id for item_id in item_ids if item_id in owned}

    async def persist_look(self, look: SavedLookSummary) -> SavedLookSummary:
        self.looks[look.id] = look
        return look

    async def get_look(
        self, user_id: UUID, look_id: UUID
    ) -> SavedLookSummary | None:
        look = self.looks.get(look_id)
        if look and look.user_id == user_id:
            return look
        return None

    async def list_looks(self, user_id: UUID) -> list[SavedLookSummary]:
        return [look for look in self.looks.values() if look.user_id == user_id]

    async def delete_look(self, user_id: UUID, look_id: UUID) -> bool:
        look = self.looks.get(look_id)
        if look and look.user_id == user_id:
            del self.looks[look_id]
            return True
        return False


def test_save_wardrobe_item_request_discriminates_product_and_vto() -> None:
    prod_req = SaveWardrobeItemRequest(
        item_type=WardrobeItemType.PRODUCT,
        product_id=uuid4(),
        offer_id=uuid4(),
    )
    assert prod_req.item_type == WardrobeItemType.PRODUCT

    with pytest.raises(ValidationError):
        SaveWardrobeItemRequest(
            item_type=WardrobeItemType.PRODUCT,
            product_id=uuid4(),
        )

    with pytest.raises(ValidationError):
        SaveWardrobeItemRequest(
            item_type=WardrobeItemType.VTO_RESULT,
            product_id=uuid4(),
            tryon_job_id=uuid4(),
        )


def test_create_saved_look_rejects_blank_title_and_foreign_items() -> None:
    with pytest.raises(ValidationError):
        CreateSavedLookRequest(title="   ", item_ids=[uuid4()])

    user_a = uuid4()
    user_b = uuid4()
    item_a = uuid4()
    item_b = uuid4()
    repo = _InMemoryLookRepo({user_a: {item_a}, user_b: {item_b}})

    # Account A cannot include Account B's item
    with pytest.raises(LookOwnershipError):
        _run(
            create_saved_look_for_user(
                repo,
                user_a,
                CreateSavedLookRequest(
                    title="Weekend Casual",
                    item_ids=[item_a, item_b],
                ),
            )
        )
    assert len(repo.looks) == 0

    # Account A can create a look with its own deduplicated items
    created = _run(
        create_saved_look_for_user(
            repo,
            user_a,
            CreateSavedLookRequest(
                title="  Weekend Casual  ",
                description="  Relaxed outfit  ",
                item_ids=[item_a, item_a],
            ),
        )
    )
    assert created.title == "Weekend Casual"
    assert created.item_count == 1
    assert _run(repo.get_look(user_b, created.id)) is None
