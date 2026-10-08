from __future__ import annotations

from asyncio import to_thread
from uuid import UUID

from api.app.core.errors import ConflictError, NotFoundError
from api.app.core.idempotency import request_fingerprint
from api.app.core.settings import get_settings
from api.app.core.transactions import transaction
from api.app.repositories.idempotency import IdempotencyRepository
from api.app.tryon.domain.artifact import compute_artifact_key
from api.app.tryon.domain.state_machine import can_transition
from api.app.tryon.integrations.catalog_client import LocalCatalogTryOnClient
from api.app.tryon.integrations.profile_client import LocalProfileTryOnClient
from api.app.tryon.repositories.tryon import TryOnRepository
from api.app.profile.integrations.r2_client import R2StorageClient
from schemas.tryon.job import TryOnCreate, TryOnCreateResponse, TryOnStatusResponse, TryOnCancelResponse


class TryOnApplicationService:
    def __init__(self, *, repository: TryOnRepository, profile: LocalProfileTryOnClient, catalog: LocalCatalogTryOnClient, queue, storage: R2StorageClient):
        self.repository = repository
        self.profile = profile
        self.catalog = catalog
        self.queue = queue
        self.storage = storage
        self.settings = get_settings()

    async def create(self, *, user_id: UUID, request: TryOnCreate, idempotency_key: str) -> TryOnCreateResponse:
        if not idempotency_key.strip():
            raise ConflictError("Idempotency-Key is required")
        fingerprint = request_fingerprint(request.product_id, self.settings.tryon_model_version, self.settings.tryon_pipeline_version, self.settings.tryon_configuration_hash)
        async with transaction(self.repository.session):
            idem = IdempotencyRepository(self.repository.session)
            existing = await idem.get(user_id=user_id, key=idempotency_key)
            if existing:
                if existing.request_hash != fingerprint:
                    raise ConflictError("Idempotency-Key was already used with a different request")
                existing_job = await self.repository.get_by_idempotency(user_id=user_id, key=idempotency_key)
                if existing_job is None:
                    raise ConflictError("Idempotency record exists without a try-on job")
                result_url = None
                if existing_job.status == "completed":
                    artifact = await self.repository.get_artifact_for_job(existing_job.id)
                    if artifact and artifact.quality_status == "accepted":
                        result_url, _ = await to_thread(self.storage.create_download_url, key=artifact.result_key, expires_in=self.settings.tryon_result_url_ttl_seconds)
                return TryOnCreateResponse(job_id=existing_job.id, status=existing_job.status, cache_hit=True, result_url=result_url)

            # Product lookup is the authoritative source for the garment version and image.
            garment = await self.catalog.get_garment_for_tryon(garment_id=request.product_id)
            # User's accepted photo is selected from the profile readiness artifact.
            photo_id = await self._get_ready_photo_id(user_id)
            photo = await self.profile.get_accepted_photo(user_id=user_id, photo_id=photo_id)
            artifact_key = compute_artifact_key(
                photo_id=photo_id,
                photo_version=photo["version"],
                garment_id=request.product_id,
                garment_version=garment["version"],
                model_version=self.settings.tryon_model_version,
                pipeline_version=self.settings.tryon_pipeline_version,
                configuration_hash=self.settings.tryon_configuration_hash,
            )
            existing_artifact_job = await self.repository.get_by_artifact_key(artifact_key)
            if existing_artifact_job is not None:
                result_url = None
                if existing_artifact_job.status == "completed":
                    artifact = await self.repository.get_artifact_for_job(existing_artifact_job.id)
                    if artifact and artifact.quality_status == "accepted":
                        result_url, _ = await to_thread(self.storage.create_download_url, key=artifact.result_key, expires_in=self.settings.tryon_result_url_ttl_seconds)
                await idem.create_claim(user_id=user_id, key=idempotency_key, request_hash=fingerprint)
                record = await idem.get(user_id=user_id, key=idempotency_key)
                response_status = existing_artifact_job.status
                response_code = 200 if response_status == "completed" else 202
                response = TryOnCreateResponse(job_id=existing_artifact_job.id, status=response_status, cache_hit=True, result_url=result_url)
                if record:
                    await idem.complete(record, status_code=response_code, response_body=response.model_dump(mode="json"))
                return response

            job = await self.repository.create_job(
                user_id=user_id,
                garment_id=request.product_id,
                profile_photo_id=photo_id,
                idempotency_key=idempotency_key,
                artifact_key=artifact_key,
                status="queued",
                model_version=self.settings.tryon_model_version,
                pipeline_version=self.settings.tryon_pipeline_version,
                photo_version=photo["version"],
                garment_version=garment["version"],
                configuration_hash=self.settings.tryon_configuration_hash,
                queue_name=self.settings.tryon_queue_name,
            )
            await idem.create_claim(user_id=user_id, key=idempotency_key, request_hash=fingerprint)
            await self.queue.enqueue(queue=self.settings.tryon_queue_name, payload={"job_id": str(job.id), "user_id": str(user_id)})
            return TryOnCreateResponse(job_id=job.id, status="queued", cache_hit=False)

    async def _get_ready_photo_id(self, user_id: UUID) -> UUID:
        from sqlalchemy import select
        from database.models.identity import UserPhoto
        stmt = select(UserPhoto).where(UserPhoto.user_id == user_id, UserPhoto.photo_type == "tryon_reference", UserPhoto.status == "accepted", UserPhoto.ready_for_tryon.is_(True)).order_by(UserPhoto.created_at.desc())
        photo = (await self.repository.session.execute(stmt)).scalars().first()
        if photo is None:
            raise NotFoundError("No accepted try-on reference photo is available")
        return photo.id

    async def prepare_execution(self, *, job_id: UUID) -> dict:
        async with transaction(self.repository.session):
            job = await self.repository.get_by_id(job_id)
            if job is None:
                raise NotFoundError("Try-on job not found")
            if job.status != "processing":
                raise ConflictError(f"Try-on job is not executable from state '{job.status}'")
            photo = await self.profile.get_accepted_photo(user_id=job.user_id, photo_id=job.profile_photo_id)
            garment = await self.catalog.get_garment_for_tryon(garment_id=job.garment_id)
            return {
                "job_id": job.id,
                "user_id": job.user_id,
                "photo_key": photo["storage_key"],
                "garment_image_key": garment["image_key"],
                "model_version": job.model_version,
                "pipeline_version": job.pipeline_version,
                "artifact_key": job.artifact_key,
                "photo_version": job.photo_version,
                "garment_version": job.garment_version,
            }

    async def set_provider_job(self, *, job_id: UUID, provider_job_id: str) -> None:
        async with transaction(self.repository.session):
            job = await self.repository.get_by_id(job_id)
            if job is None:
                raise NotFoundError("Try-on job not found")
            job.provider_job_id = provider_job_id
            job.status = "inference"

    async def worker_claim(self, job_id: UUID):
        async with transaction(self.repository.session):
            job = await self.repository.claim_job(job_id)
            if job is None:
                return None
            return {
                "job_id": job.id,
                "user_id": job.user_id,
                "profile_photo_id": job.profile_photo_id,
                "garment_id": job.garment_id,
                "status": job.status,
                "artifact_key": job.artifact_key,
                "model_version": job.model_version,
                "pipeline_version": job.pipeline_version,
                "photo_version": job.photo_version,
                "garment_version": job.garment_version,
            }

    async def worker_progress(self, *, job_id: UUID, status: str) -> None:
        async with transaction(self.repository.session):
            job = await self.repository.get_by_id(job_id)
            if job is None:
                raise NotFoundError("Try-on job not found")
            if not can_transition(job.status, status):
                raise ConflictError(f"Invalid Try-on state transition: {job.status} -> {status}")
            job.status = status

    async def worker_complete(self, *, job_id: UUID, result_key: str, quality: dict) -> dict:
        if not result_key.startswith("tryon-results/"):
            raise ConflictError("Try-on result must use the tryon-results/ storage prefix")
        async with transaction(self.repository.session):
            job = await self.repository.get_by_id(job_id)
            if job is None:
                raise NotFoundError("Try-on job not found")
            if not can_transition(job.status, "completed"):
                raise ConflictError(f"Invalid Try-on completion from state '{job.status}'")
            if quality.get("quality_status") != "accepted":
                raise ConflictError("Try-on result did not pass quality validation")
            artifact = await self.repository.complete(job, result_key=result_key, quality=quality)
            return {"job_id": job.id, "artifact_id": artifact.id, "status": job.status}

    async def worker_fail(self, *, job_id: UUID, reason: str, retryable: bool) -> dict:
        async with transaction(self.repository.session):
            job = await self.repository.get_by_id(job_id)
            if job is None:
                raise NotFoundError("Try-on job not found")
            should_retry = await self.repository.fail(job, reason=reason, retryable=retryable)
            return {"job_id": job.id, "status": job.status, "retry": should_retry}

    async def get_status(self, *, user_id: UUID, job_id: UUID) -> TryOnStatusResponse:
        async with transaction(self.repository.session):
            job = await self.repository.get_by_id_for_user(user_id=user_id, job_id=job_id)
            if job is None:
                raise NotFoundError("Try-on job not found")
            result_url = None
            if job.status == "completed":
                artifact = await self.repository.get_artifact_for_job(job.id)
                if artifact:
                    result_url, _ = await to_thread(self.storage.create_download_url, key=artifact.result_key, expires_in=self.settings.tryon_result_url_ttl_seconds)
            result_meta = None
            artifact = await self.repository.get_artifact_for_job(job.id)
            if artifact is not None:
                from schemas.tryon.result import TryOnResultMetadata
                result_meta = TryOnResultMetadata(
                    artifact_id=artifact.id, quality_status=artifact.quality_status, quality_score=artifact.quality_score,
                    width=artifact.width, height=artifact.height, size_bytes=artifact.size_bytes,
                    content_type=artifact.content_type, content_sha256=artifact.content_sha256,
                    quality_reasons=artifact.quality_reasons or [], result_url=result_url,
                )
            return TryOnStatusResponse(job_id=job.id, status=job.status, result_url=result_url, failure_reason=job.failure_reason, model_version=job.model_version, pipeline_version=job.pipeline_version, attempt_count=job.attempt_count, result=result_meta)

    async def cancel(self, *, user_id: UUID, job_id: UUID) -> TryOnCancelResponse:
        async with transaction(self.repository.session):
            job = await self.repository.get_by_id_for_user(user_id=user_id, job_id=job_id)
            if job is None:
                raise NotFoundError("Try-on job not found")
            await self.repository.cancel(job)
            return TryOnCancelResponse(job_id=job.id, status=job.status)
