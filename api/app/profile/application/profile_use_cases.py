from __future__ import annotations

from uuid import UUID

from api.app.core.errors import NotFoundError
from api.app.core.transactions import transaction
from api.app.profile.repositories.profile import ProfileRepository


class ProfileApplicationService:
    def __init__(self, repository: ProfileRepository) -> None:
        self.repository = repository

    async def create_user(self) -> UUID:
        async with transaction(self.repository.session):
            user = await self.repository.create_user()
            return user.id

    async def update_body(
        self,
        user_id: UUID,
        *,
        height_cm: int | None,
        weight_kg: int | None,
        build: str | None,
    ) -> int:
        async with transaction(self.repository.session):
            if await self.repository.get_user(user_id) is None:
                raise NotFoundError("User not found")
            profile = await self.repository.upsert_body(
                user_id,
                height_cm=height_cm,
                weight_kg=weight_kg,
                build=build,
            )
            return profile.version
