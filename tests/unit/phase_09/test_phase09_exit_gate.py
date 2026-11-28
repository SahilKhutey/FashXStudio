from __future__ import annotations

from collections.abc import Coroutine
from typing import Any
from uuid import UUID, uuid4

import pytest

from fashx.catalog.detail.redirect_validator import validate_merchant_url
from fashx.commerce_wardrobe.looks.schemas import (
    CreateSavedLookRequest,
    SavedLookSummary,
)
from fashx.commerce_wardrobe.looks.service import (
    SavedLookRepositoryProtocol,
    create_saved_look_for_user,
)
from fashx.main import create_app


def _run[T](coro: Coroutine[Any, Any, T]) -> T:
    """Step an async coroutine synchronously without spawning an event-loop socketpair."""
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise RuntimeError("Unexpected await suspension in synchronous Phase 09 exit-gate test")


def test_phase09_shopper_routes_are_mounted() -> None:
    app = create_app()
    paths = set(app.openapi()["paths"].keys())
    expected_routes = {
        "/api/v1/me",
        "/api/v1/profile/me",
        "/api/v1/onboarding/style-quiz",
        "/api/v1/search/products",
        "/api/v1/feed",
        "/api/v1/tryon/jobs",
        "/api/v1/wardrobe/items",
    }
    missing = expected_routes - paths
    assert not missing, f"Missing Phase 09 routes: {sorted(missing)}"


def test_phase09_merchant_redirect_validator_blocks_unsafe_urls() -> None:
    verified = {"merchant.example.com"}
    assert (
        validate_merchant_url(
            "https://merchant.example.com/p/123?utm_source=fashx",
            verified,
        )
        == "https://merchant.example.com/p/123?utm_source=fashx"
    )
    for bad_url in (
        "javascript:alert(1)",
        "http://merchant.example.com/insecure",
        "https://127.0.0.1/internal",
        "https://localhost/admin",
        "https://evil.example.org/p/123",
    ):
        with pytest.raises(ValueError):
            validate_merchant_url(bad_url, verified)


def test_phase09_saved_look_creation_contract() -> None:
    user_id = uuid4()
    item_1 = uuid4()
    item_2 = uuid4()

    class _FakeLooksRepo(SavedLookRepositoryProtocol):
        async def get_owned_item_ids(
            self, user_id: UUID, item_ids: list[UUID]
        ) -> set[UUID]:
            return set(item_ids)

        async def persist_look(self, look: SavedLookSummary) -> SavedLookSummary:
            return look

        async def get_look(
            self, user_id: UUID, look_id: UUID
        ) -> SavedLookSummary | None:
            return None

        async def list_looks(self, user_id: UUID) -> list[SavedLookSummary]:
            return []

        async def delete_look(self, user_id: UUID, look_id: UUID) -> bool:
            return True

    result = _run(
        create_saved_look_for_user(
            _FakeLooksRepo(),
            user_id=user_id,
            payload=CreateSavedLookRequest(
                title="Autumn Capsule",
                description="Blazer + Trousers",
                item_ids=[item_1, item_2],
            ),
        )
    )
    assert result.user_id == user_id
    assert result.title == "Autumn Capsule"
    assert result.item_count == 2
    assert result.item_ids == [item_1, item_2]
