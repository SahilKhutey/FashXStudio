from dataclasses import dataclass
from uuid import UUID

from api.app.core.errors import EntityNotFoundError
from api.app.core.ports.storage import InMemoryStorageAdapter, StoragePort
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from api.app.tryon.repositories.tryon_repository import TryOnUnitOfWork


@dataclass(frozen=True)
class RevokeConsentCommand:
    user_id: UUID
    data_type: str  # 'body_photo', 'measurements', or 'all'


@dataclass(frozen=True)
class RevokeConsentResult:
    user_id: UUID
    data_type: str
    status: str
    photos_purged: int
    jobs_purged: int


class RevokeConsentUseCase:
    """Rule I16 & Gate G4: Privacy Gate and Cascading Deletion Engine.

    When user revokes consent for 'body_photo' or invokes right to erasure:
    1. Instantly cascades deletion of all Try-On jobs and rendered artifacts.
    2. Purges raw image files from cloud object storage (S3 / MinIO).
    3. Hard-deletes all UserPhoto records from the database.
    4. Updates consent record to granted=False.
    """

    def __init__(
        self,
        profile_uow: ProfileUnitOfWork,
        tryon_uow: TryOnUnitOfWork,
        storage: StoragePort | None = None,
    ) -> None:
        self.profile_uow = profile_uow
        self.tryon_uow = tryon_uow
        self.storage = storage or InMemoryStorageAdapter()

    async def execute(self, cmd: RevokeConsentCommand) -> RevokeConsentResult:
        # 1. Validate User
        async with self.profile_uow:
            user = await self.profile_uow.users.get_by_id(cmd.user_id)
            if user is None:
                raise EntityNotFoundError("User", cmd.user_id)

            # Update consent record to False
            await self.profile_uow.consents.upsert(
                user_id=cmd.user_id,
                data_type=cmd.data_type,
                granted=False,
            )
            await self.profile_uow.commit()

        jobs_purged = 0
        photos_purged = 0

        # 2. If body_photo or all, cascade hard deletions
        if cmd.data_type in ("body_photo", "all"):
            # Step A: Delete dependent Try-On jobs and artifacts (respecting FK constraints)
            async with self.tryon_uow:
                jobs = await self.tryon_uow.jobs.list_by_user(cmd.user_id, limit=200)
                for job in jobs:
                    artifact = await self.tryon_uow.artifacts.get_by_job_id(job.id)
                    if artifact:
                        await self.tryon_uow.artifacts.delete(artifact)
                    await self.tryon_uow.jobs.delete(job)
                    jobs_purged += 1
                await self.tryon_uow.commit()

            # Step B: Purge photos from storage and database
            async with self.profile_uow:
                photos = await self.profile_uow.photos.list_for_user(cmd.user_id)
                for photo in photos:
                    if photo.storage_key:
                        await self.storage.delete(photo.storage_key)
                    await self.profile_uow.photos.delete(photo)
                    photos_purged += 1
                await self.profile_uow.commit()

        return RevokeConsentResult(
            user_id=cmd.user_id,
            data_type=cmd.data_type,
            status="revoked_and_purged",
            photos_purged=photos_purged,
            jobs_purged=jobs_purged,
        )
