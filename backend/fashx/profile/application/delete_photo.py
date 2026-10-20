"""Single user photo deletion with cascading derived try-on job and result media removal.

Privacy & DPDP rule:
When a user deletes a photo, derived biometric artifacts (try-on jobs, rendered results,
and media objects) must die with the source photo, while other photos and jobs remain intact.
Storage object purging is enqueued transactionally via the outbox.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fashx.security.errors import ApiError


async def delete_user_photo(uow: Any, user_id: UUID, photo_id: UUID) -> None:
    """Delete a single photo, cascade derived jobs/artifacts, and enqueue storage purge via outbox."""
    photo = await uow.photos.get_owned(photo_id, user_id)
    if photo is None:
        raise ApiError(404, "not_found", "Photo not found")

    keys = await uow.media.keys_derived_from_photo(photo_id)
    await uow.media.delete_for_photo(photo_id)
    await uow.photos.delete(photo)
    await uow.outbox.add("storage.delete_keys", {"keys": keys})
