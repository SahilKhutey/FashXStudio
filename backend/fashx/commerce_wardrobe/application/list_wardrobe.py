from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from database.models.tryon import TryOnArtifact
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)


@dataclass(frozen=True)
class WardrobeItemView:
    id: UUID
    item_id: UUID
    user_id: UUID
    garment_id: UUID
    title_at_save: str
    price_at_save: int
    currency: str
    snapshot_title: str
    snapshot_price_minor: int
    snapshot_currency: str
    snapshot_image_key: str
    tryon_artifact_id: UUID | None
    saved_at: str
    purchased_at: str | None
    fit_feedback_given: bool
    current_price: int | None
    render: dict[str, Any] | None


class ListWardrobeUseCase:
    """Lists saved wardrobe items for a user with live price and signed render."""

    def __init__(
        self,
        uow: CommerceWardrobeUnitOfWork,
        catalog_uow: CatalogUnitOfWork | None = None,
        storage: Any | None = None,
    ) -> None:
        self.uow = uow
        self.catalog_uow = catalog_uow
        self.storage = storage

    async def execute(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[WardrobeItemView]:
        async with self.uow:
            db_items = await self.uow.wardrobe.list_for_user(user_id, limit=limit, offset=offset)
            feedbacks = await self.uow.fit_feedback.list_for_user(user_id)
            feedback_garment_ids = {f.garment_id for f in feedbacks}

            # Batch lookup artifacts for renders
            artifacts_by_id: dict[UUID, TryOnArtifact] = {}
            artifact_ids = [item.tryon_artifact_id for item in db_items if item.tryon_artifact_id]
            if artifact_ids:
                from sqlalchemy import select

                stmt = select(TryOnArtifact).where(TryOnArtifact.id.in_(artifact_ids))
                res = await self.uow.session.scalars(stmt)
                artifacts_by_id = {a.id: a for a in res.all()}

            # Extract item data while session is active to avoid DetachedInstanceError
            items_data = [
                {
                    "id": item.id,
                    "user_id": item.user_id,
                    "garment_id": item.garment_id,
                    "snapshot_title": item.snapshot_title,
                    "snapshot_price_minor": item.snapshot_price_minor,
                    "snapshot_currency": item.snapshot_currency,
                    "snapshot_image_key": item.snapshot_image_key,
                    "tryon_artifact_id": item.tryon_artifact_id,
                    "saved_at": item.saved_at.isoformat() if item.saved_at else "",
                    "purchased_at": item.purchased_at.isoformat() if item.purchased_at else None,
                    "fit_feedback_given": item.garment_id in feedback_garment_ids,
                    "artifact_result_key": (
                        artifacts_by_id[item.tryon_artifact_id].result_key
                        if item.tryon_artifact_id in artifacts_by_id
                        else None
                    ),
                }
                for item in db_items
            ]

        # Live current price lookup
        current_prices: dict[UUID, int | None] = {}
        if self.catalog_uow:
            async with self.catalog_uow:
                for d in items_data:
                    gid = d["garment_id"]
                    if gid not in current_prices:
                        garment = await self.catalog_uow.canonical_garments.get_by_id(gid)
                        if garment is None:
                            current_prices[gid] = None
                        else:
                            offers = await self.catalog_uow.offers.list_for_garment(gid)
                            current_prices[gid] = offers[0].price_minor if offers else None

        results: list[WardrobeItemView] = []
        now_ts = int(time.time())
        for d in items_data:
            render: dict[str, Any] | None = None
            res_key = d["artifact_result_key"]
            if res_key:
                if self.storage and hasattr(self.storage, "signed_get_url"):
                    url = self.storage.signed_get_url(res_key, ttl_s=3600)
                    render = {"url": url, "expires_at": now_ts + 3600}
                elif self.storage and hasattr(self.storage, "get_signed_url"):
                    url = await self.storage.get_signed_url(res_key, expires_in_seconds=3600)
                    render = {"url": url, "expires_at": now_ts + 3600}

            curr_price = current_prices.get(d["garment_id"])

            results.append(
                WardrobeItemView(
                    id=d["id"],
                    item_id=d["id"],
                    user_id=d["user_id"],
                    garment_id=d["garment_id"],
                    title_at_save=d["snapshot_title"],
                    price_at_save=d["snapshot_price_minor"],
                    currency=d["snapshot_currency"],
                    snapshot_title=d["snapshot_title"],
                    snapshot_price_minor=d["snapshot_price_minor"],
                    snapshot_currency=d["snapshot_currency"],
                    snapshot_image_key=d["snapshot_image_key"],
                    tryon_artifact_id=d["tryon_artifact_id"],
                    saved_at=d["saved_at"],
                    purchased_at=d["purchased_at"],
                    fit_feedback_given=d["fit_feedback_given"],
                    current_price=curr_price,
                    render=render,
                )
            )

        return results
