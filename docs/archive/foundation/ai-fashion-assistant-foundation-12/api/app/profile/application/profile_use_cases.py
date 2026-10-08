from __future__ import annotations

from uuid import UUID

from api.app.core.errors import NotFoundError
from api.app.core.transactions import transaction
from api.app.profile.repositories.profile import ProfileRepository


class ProfileApplicationService:
    def __init__(self, repository: ProfileRepository) -> None:
        self.repository = repository

    async def ensure_user(self, user_id: UUID) -> UUID:
        async with transaction(self.repository.session):
            user = await self.repository.get_user(user_id)
            if user is None:
                user = await self.repository.create_user(user_id=user_id)
            return user.id

    async def update_profile(
        self,
        user_id: UUID,
        *,
        height_cm: int | None,
        weight_kg: int | None,
        build: str | None,
        colors_favored: list[str],
        colors_avoided: list[str],
        categories: list[str],
        budget_min: int | None,
        budget_max: int | None,
    ) -> UUID:
        async with transaction(self.repository.session):
            if await self.repository.get_user(user_id) is None:
                await self.repository.create_user(user_id=user_id)
            await self.repository.upsert_body(
                user_id,
                height_cm=height_cm,
                weight_kg=weight_kg,
                build=build,
            )
            await self.repository.upsert_preferences(
                user_id,
                colors_favored=colors_favored,
                colors_avoided=colors_avoided,
                categories=categories,
                budget_min=budget_min,
                budget_max=budget_max,
            )
            return user_id

    async def get_profile(self, user_id: UUID) -> tuple[object, object, object]:
        async with transaction(self.repository.session):
            user = await self.repository.get_user(user_id)
            if user is None:
                raise NotFoundError("User not found")
            body, preferences, style = await self.repository.get_derived_rows(user_id)
            return user, body, preferences

    async def get_derived(self, user_id: UUID) -> tuple[object, object, object]:
        user, body, preferences = await self.get_profile(user_id)
        style = await self.repository.get_style(user_id)
        return body, preferences, style
