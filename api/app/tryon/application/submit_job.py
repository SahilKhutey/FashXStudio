from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from api.app.core.errors import ConsentRequiredError, EntityNotFoundError, ValidationError
from api.app.profile.repositories.profile_repository import ProfileUnitOfWork
from api.app.tryon.adapters.mock_adapter import MockTryOnAdapter
from api.app.tryon.cache_key import compute_tryon_cache_key
from api.app.tryon.ports import TryOnModelAdapterPort
from api.app.tryon.repositories.tryon_repository import TryOnUnitOfWork
from database.models.tryon import TryOnJob


@dataclass(frozen=True)
class SubmitTryOnJobCommand:
    user_id: UUID
    garment_id: UUID
    idempotency_key: str
    render_config: dict[str, Any] | None = None


@dataclass(frozen=True)
class SubmitTryOnJobResult:
    job_id: UUID
    status: str
    artifact_key: str
    is_cached: bool
    result_url: str | None = None


class SubmitTryOnJobUseCase:
    """Orchestrates Try-On job submission, Pre-Inference Quality & Consent Gate, and composite caching."""

    def __init__(
        self,
        tryon_uow: TryOnUnitOfWork,
        profile_uow: ProfileUnitOfWork,
        catalog_uow: CatalogUnitOfWork,
        adapter: TryOnModelAdapterPort | None = None,
    ) -> None:
        self.tryon_uow = tryon_uow
        self.profile_uow = profile_uow
        self.catalog_uow = catalog_uow
        self.adapter = adapter or MockTryOnAdapter()

    async def execute(self, cmd: SubmitTryOnJobCommand) -> SubmitTryOnJobResult:
        # 1. Pre-Inference Consent & Quality Gate (Rule I07)
        async with self.profile_uow:
            user = await self.profile_uow.users.get_by_id(cmd.user_id)
            if user is None:
                raise EntityNotFoundError("User", cmd.user_id)

            has_consent = await self.profile_uow.consents.has_consent(cmd.user_id, "body_photo")
            if not has_consent:
                raise ConsentRequiredError("body_photo")

            photo = await self.profile_uow.photos.get_active_photo(cmd.user_id, "tryon_reference")
            if photo is None:
                raise ValidationError(
                    "User does not have an active portrait photo uploaded.",
                    field="photo",
                )
            if photo.status != "accepted":
                raise ValidationError(
                    f"User portrait photo status is '{photo.status}'; must be 'accepted' to run try-on.",
                    field="photo_status",
                )
            photo_id = photo.id
            photo_storage_key = photo.storage_key

        # 2. Garment Validation
        async with self.catalog_uow:
            garment = await self.catalog_uow.canonical_garments.get_by_id(cmd.garment_id)
            if garment is None:
                raise EntityNotFoundError("CanonicalGarment", cmd.garment_id)
            garment_id = garment.id
            garment_version = garment.version

        # 3. Compute Deterministic Composite Cache Key (Roadmap 4.4)
        artifact_key = compute_tryon_cache_key(
            user_photo_hash=photo_storage_key,
            garment_id=garment_id,
            garment_version=garment_version,
            model_version=self.adapter.model_version,
            pipeline_version=self.adapter.pipeline_version,
            render_config=cmd.render_config,
        )

        async with self.tryon_uow:
            # 4. Check Idempotency
            existing_job = await self.tryon_uow.jobs.get_by_user_and_idempotency(
                cmd.user_id, cmd.idempotency_key
            )
            if existing_job:
                # If existing job has an artifact, fetch it
                artifact = await self.tryon_uow.artifacts.get_by_artifact_key(
                    existing_job.artifact_key
                )
                return SubmitTryOnJobResult(
                    job_id=existing_job.id,
                    status=existing_job.status,
                    artifact_key=existing_job.artifact_key,
                    is_cached=existing_job.status == "completed",
                    result_url=artifact.result_key if artifact else None,
                )

            # 5. Check Artifact Cache Invalidation Key
            cached_artifact = await self.tryon_uow.artifacts.get_by_artifact_key(artifact_key)
            if cached_artifact:
                # Instant cache hit: Return cached artifact result directly (Rule I10 / Roadmap 4.4)
                return SubmitTryOnJobResult(
                    job_id=cached_artifact.job_id,
                    status="completed",
                    artifact_key=artifact_key,
                    is_cached=True,
                    result_url=cached_artifact.result_key,
                )

            # 6. Enqueue New Asynchronous Job (Rule I06)
            job = TryOnJob(
                user_id=cmd.user_id,
                garment_id=garment_id,
                profile_photo_id=photo_id,
                idempotency_key=cmd.idempotency_key,
                artifact_key=artifact_key,
                status="queued",
                model_version=self.adapter.model_version,
                pipeline_version=self.adapter.pipeline_version,
            )
            self.tryon_uow.jobs.add(job)
            await self.tryon_uow.commit()

            return SubmitTryOnJobResult(
                job_id=job.id,
                status="queued",
                artifact_key=artifact_key,
                is_cached=False,
                result_url=None,
            )
