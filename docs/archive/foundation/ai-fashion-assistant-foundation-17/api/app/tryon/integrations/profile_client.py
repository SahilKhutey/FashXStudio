from __future__ import annotations

from uuid import UUID

from api.app.core.errors import NotFoundError
from api.app.profile.repositories.media import ProfileMediaRepository


class LocalProfileTryOnClient:
    """Modular-monolith adapter; production microservice extraction can replace this with HTTP."""

    def __init__(self, repository: ProfileMediaRepository) -> None:
        self.repository = repository

    async def get_accepted_photo(self, *, user_id: UUID, photo_id: UUID) -> dict:
        photo = await self.repository.get_photo(user_id, photo_id)
        if photo is None:
            raise NotFoundError("Try-on profile photo not found")
        if photo.status != "accepted" or not photo.ready_for_tryon:
            raise NotFoundError("Try-on profile photo is not ready")
        return {
            "photo_id": photo.id,
            "storage_key": photo.storage_key,
            "version": photo.version,
            "user_id": photo.user_id,
        }
