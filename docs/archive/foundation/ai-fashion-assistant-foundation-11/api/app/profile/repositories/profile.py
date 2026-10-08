from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.identity import User
from database.models.profile import BodyProfile, UserPreference, UserStyleProfile


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def create_user(self, *, user_id: UUID | None = None) -> User:
        user = User()
        if user_id is not None:
            user.id = user_id
        self.session.add(user)
        await self.session.flush()
        return user

    async def upsert_body(self, user_id: UUID, *, height_cm: int | None, weight_kg: int | None, build: str | None) -> BodyProfile:
        current = await self.session.get(BodyProfile, user_id)
        if current is None:
            current = BodyProfile(user_id=user_id, version=1)
            self.session.add(current)
        else:
            current.version += 1
        current.height_cm = height_cm
        current.weight_kg = weight_kg
        current.build = build
        await self.session.flush()
        return current

    async def get_body(self, user_id: UUID) -> BodyProfile | None:
        return await self.session.get(BodyProfile, user_id)

    async def upsert_preferences(
        self,
        user_id: UUID,
        *,
        colors_favored: list[str],
        colors_avoided: list[str],
        categories: list[str],
        budget_min: int | None,
        budget_max: int | None,
    ) -> UserPreference:
        current = await self.session.get(UserPreference, user_id)
        if current is None:
            current = UserPreference(user_id=user_id)
            self.session.add(current)
        current.colors_favored = colors_favored
        current.colors_avoided = colors_avoided
        current.categories = categories
        current.budget_min = budget_min
        current.budget_max = budget_max
        await self.session.flush()
        return current

    async def get_style(self, user_id: UUID) -> UserStyleProfile | None:
        return await self.session.get(UserStyleProfile, user_id)

    async def get_derived_rows(self, user_id: UUID) -> tuple[BodyProfile | None, UserPreference | None, UserStyleProfile | None]:
        body = await self.session.get(BodyProfile, user_id)
        preferences = await self.session.get(UserPreference, user_id)
        style = await self.session.get(UserStyleProfile, user_id)
        return body, preferences, style
