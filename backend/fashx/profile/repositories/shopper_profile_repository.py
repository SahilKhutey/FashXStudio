from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.profile import ProfileCategorySize, ShopperProfile


class ShopperProfileRepository:
    """Repository handling persistence for ShopperProfile and category sizing preferences."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_user_id(self, user_id: UUID) -> ShopperProfile | None:
        stmt = select(ShopperProfile).where(ShopperProfile.user_id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, profile_id: UUID) -> ShopperProfile | None:
        stmt = select(ShopperProfile).where(ShopperProfile.id == profile_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user_id: UUID, data: dict[str, Any]) -> ShopperProfile:
        now = datetime.now(UTC)
        profile = ShopperProfile(
            id=uuid4(),
            user_id=user_id,
            height_cm=data.get("height_cm"),
            weight_kg=data.get("weight_kg"),
            preferred_size_system=data.get("preferred_size_system"),
            preferred_fit=data.get("preferred_fit"),
            style_preferences=data.get("style_preferences", []),
            preferred_colors=data.get("preferred_colors", []),
            product_categories=data.get("product_categories", []),
            shopping_preferences=data.get("shopping_preferences", {}),
            version=1,
            created_at=now,
            updated_at=now,
        )
        self._db.add(profile)
        await self._db.commit()
        await self._db.refresh(profile)
        return profile

    async def update_profile(
        self,
        profile_id: UUID,
        changes: dict[str, Any],
        expected_version: int | None = None,
    ) -> tuple[ShopperProfile | None, bool]:
        """Updates profile with optimistic locking. Returns (updated_profile, conflict_detected)."""
        now = datetime.now(UTC)

        stmt = update(ShopperProfile).where(ShopperProfile.id == profile_id)
        if expected_version is not None:
            stmt = stmt.where(ShopperProfile.version == expected_version)

        # Prepare values
        update_vals = {
            "version": ShopperProfile.version + 1,
            "updated_at": now,
        }
        for field, val in changes.items():
            if field in (
                "height_cm",
                "weight_kg",
                "preferred_size_system",
                "preferred_fit",
                "style_preferences",
                "preferred_colors",
                "product_categories",
                "shopping_preferences",
            ):
                update_vals[field] = val

        stmt = stmt.values(**update_vals)
        result = await self._db.execute(stmt)
        await self._db.commit()

        if result.rowcount == 0:
            if expected_version is not None:
                # Version mismatch -> conflict
                return None, True
            return None, False

        updated = await self.get_by_id(profile_id)
        return updated, False

    async def get_category_sizes(self, user_id: UUID) -> list[ProfileCategorySize]:
        stmt = (
            select(ProfileCategorySize)
            .where(ProfileCategorySize.user_id == user_id)
            .order_by(ProfileCategorySize.category_code)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def set_category_sizes(
        self, user_id: UUID, sizes: list[dict[str, str]]
    ) -> list[ProfileCategorySize]:
        now = datetime.now(UTC)
        # Replace existing category sizes for this user
        del_stmt = delete(ProfileCategorySize).where(ProfileCategorySize.user_id == user_id)
        await self._db.execute(del_stmt)

        results = []
        for item in sizes:
            cat_size = ProfileCategorySize(
                id=uuid4(),
                user_id=user_id,
                category_code=item["category_code"],
                size_system=item["size_system"],
                size_label=item["size_label"],
                updated_at=now,
            )
            self._db.add(cat_size)
            results.append(cat_size)

        await self._db.commit()
        return results
