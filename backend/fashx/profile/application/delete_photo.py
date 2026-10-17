"""Single user photo deletion with cascading derived try-on job and result media removal.

Privacy & DPDP rule:
When a user deletes a photo, derived biometric artifacts (try-on jobs, rendered results,
and media objects) must die with the source photo, while other photos and jobs remain intact.
"""

from __future__ import annotations

import inspect
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.identity import UserPhoto
from database.models.media import MediaObject
from database.models.tryon import TryOnArtifact, TryOnJob


async def delete_user_photo(
    session: AsyncSession,
    *,
    user_id: UUID,
    photo_id: UUID,
    storage: Any | None = None,
) -> bool:
    """Delete a single photo and cascade deletion of derived try-on jobs and result media.

    Returns True if photo existed and was deleted, False if not found.
    """
    # 1. Fetch photo
    stmt = select(UserPhoto).where(UserPhoto.id == photo_id, UserPhoto.user_id == user_id)
    photo = (await session.scalars(stmt)).first()
    if photo is None:
        return False

    # 2. Find all try-on jobs derived from this photo
    jobs_stmt = select(TryOnJob).where(TryOnJob.profile_photo_id == photo_id)
    jobs = (await session.scalars(jobs_stmt)).all()
    job_ids = [j.id for j in jobs]

    # 3. Collect storage keys to purge
    keys_to_delete: set[str] = set()
    if photo.storage_key:
        keys_to_delete.add(photo.storage_key)

    for j in jobs:
        if j.artifact_key:
            keys_to_delete.add(j.artifact_key)

    if job_ids:
        art_stmt = select(TryOnArtifact).where(TryOnArtifact.job_id.in_(job_ids))
        artifacts = (await session.scalars(art_stmt)).all()
        for art in artifacts:
            if art.artifact_key:
                keys_to_delete.add(art.artifact_key)
            if art.result_key:
                keys_to_delete.add(art.result_key)

    # 4. Delete media_objects rows associated with the photo or derived results
    if keys_to_delete:
        del_media_stmt = delete(MediaObject).where(
            MediaObject.user_id == user_id,
            MediaObject.object_key.in_(list(keys_to_delete)),
        )
        await session.execute(del_media_stmt)

    # 5. Delete the photo itself
    # ON DELETE CASCADE removes tryon_jobs (and cascades to tryon_artifacts) in PostgreSQL/SQLite
    await session.delete(photo)
    await session.flush()

    # 6. Purge files from object storage
    if storage is not None:
        for k in keys_to_delete:
            try:
                res = storage.delete(k)
                if inspect.isawaitable(res):
                    await res
            except Exception:
                pass

    return True
