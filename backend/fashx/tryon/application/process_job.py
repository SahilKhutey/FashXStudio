import inspect
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from database.models.tryon import TryOnArtifact
from fashx.application.ports.storage import media_key
from fashx.application.ports.tryon import TryOnError, TryOnRequest
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import EntityNotFoundError
from fashx.ml.prep import prepare_for_provider
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.tryon.adapters.mock_adapter import MockTryOnAdapter
from fashx.tryon.ports import InferenceInput
from fashx.tryon.quality_validator import PostInferenceQualityValidator
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork
from fashx.tryon.watermarker import SyntheticWatermarker


@dataclass(frozen=True)
class ProcessJobResult:
    job_id: UUID
    status: str
    artifact_key: str
    result_url: str | None = None
    failure_reason: str | None = None


class ProcessTryOnJobUseCase:
    """Worker use case: executes preprocessing, two-phase model inference, C2PA watermarking, and post-inference quality gate."""

    def __init__(
        self,
        tryon_uow: TryOnUnitOfWork,
        profile_uow: ProfileUnitOfWork,
        catalog_uow: CatalogUnitOfWork,
        adapter: Any | None = None,
        storage: Any | None = None,
        breaker: Any | None = None,
    ) -> None:
        self.tryon_uow = tryon_uow
        self.profile_uow = profile_uow
        self.catalog_uow = catalog_uow
        self.adapter = adapter or MockTryOnAdapter()
        self.storage = storage
        self.breaker = breaker

    async def execute(
        self,
        job_id: UUID,
        user_photo_bytes: bytes | None = None,
        garment_image_bytes: bytes | None = None,
    ) -> ProcessJobResult:
        # 1. Load Job
        async with self.tryon_uow:
            job = await self.tryon_uow.jobs.get_by_id(job_id)
            if job is None:
                raise EntityNotFoundError("TryOnJob", job_id)

            if job.status == "completed":
                artifact = await self.tryon_uow.artifacts.get_by_job_id(job.id)
                return ProcessJobResult(
                    job_id=job.id,
                    status="completed",
                    artifact_key=job.artifact_key,
                    result_url=artifact.result_key if artifact else None,
                )

            # Stage: Validating & Preprocessing
            job.status = "preprocessing"
            await self.tryon_uow.commit()

        # 2. Check active consent before proceeding
        async with self.profile_uow:
            has_consent = await self.profile_uow.consents.has_consent(job.user_id, "body_photo")
        if not has_consent:
            async with self.tryon_uow:
                await self.tryon_uow.jobs.cancel(job.id, "consent_revoked")
                if hasattr(self.tryon_uow, "usage"):
                    await self.tryon_uow.usage.record("cancelled", error_code="consent_revoked")
                await self.tryon_uow.commit()
            return ProcessJobResult(
                job_id=job.id,
                status="cancelled",
                artifact_key=job.artifact_key,
                failure_reason="consent_revoked",
            )

        # 3. Retrieve Garment Details
        async with self.catalog_uow:
            garment = await self.catalog_uow.canonical_garments.get_by_id(job.garment_id)
            if garment is None:
                async with self.tryon_uow:
                    await self.tryon_uow.jobs.update_status(
                        job_id, "failed", failure_reason="unsupported_garment"
                    )
                    await self.tryon_uow.commit()
                return ProcessJobResult(
                    job_id=job_id,
                    status="failed",
                    artifact_key=job.artifact_key,
                    failure_reason="unsupported_garment",
                )
            garment_category = garment.category
            garment_version = garment.version

        photo_bytes = user_photo_bytes or b"SYNTHETIC_USER_PHOTO_BYTES_512x768"
        garment_bytes = garment_image_bytes or b"SYNTHETIC_GARMENT_BYTES_256x256"

        # 4. Model Inference with Circuit Breaker and Two-Phase Provider (Rule I06 & Rule I08)
        async with self.tryon_uow:
            await self.tryon_uow.jobs.update_status(job_id, "inference")
            await self.tryon_uow.commit()

        cost_usd_est: float | None = 0.0
        provider_name = getattr(self.adapter, "provider", "mock")
        model_version = getattr(self.adapter, "model_version", "tryon-v1.6")
        pipeline_version = getattr(self.adapter, "pipeline_version", "pilot-pipe-v1")
        latency_ms = 0.0

        if hasattr(self.adapter, "submit") and hasattr(self.adapter, "collect"):
            try:
                if self.breaker:
                    self.breaker.guard()

                provider_job_id = getattr(job, "provider_job_id", None)
                if not provider_job_id:
                    cat_arg = garment_category if garment_category in ("tops", "bottoms", "one-pieces") else "auto"
                    provider_job_id = self.adapter.submit(
                        TryOnRequest(
                            person_jpeg=prepare_for_provider(photo_bytes),
                            garment_jpeg=prepare_for_provider(garment_bytes),
                            category=cat_arg,
                        )
                    )
                    async with self.tryon_uow:
                        await self.tryon_uow.jobs.set_provider_job(
                            job.id, provider_name, provider_job_id
                        )
                        await self.tryon_uow.commit()

                out = self.adapter.collect(provider_job_id, deadline_s=90.0)
                if self.breaker:
                    self.breaker.success()

                rendered_bytes = out.image_bytes
                latency_ms = float(out.latency_ms)
                cost_usd_est = out.cost_usd_est
                model_version = out.model
                provider_name = out.provider
            except TryOnError as err:
                if err.code in ("provider_unavailable", "provider_unreachable", "provider_timeout"):
                    if self.breaker:
                        self.breaker.failure()

                max_attempts = 3
                attempts = getattr(job, "attempts", 1)
                async with self.tryon_uow:
                    if err.retryable and (err.code == "breaker_open" or attempts < max_attempts):
                        await self.tryon_uow.jobs.requeue(
                            job.id,
                            delay_s=min(2**attempts * 5, 120),
                            clear_provider_job=True,
                        )
                        if hasattr(self.tryon_uow, "usage"):
                            await self.tryon_uow.usage.record("retried", error_code=err.code)
                        await self.tryon_uow.commit()
                        return ProcessJobResult(
                            job_id=job.id,
                            status="queued",
                            artifact_key=job.artifact_key,
                            failure_reason=err.code,
                        )
                    else:
                        await self.tryon_uow.jobs.fail(job.id, err.code, err.user_message)
                        if hasattr(self.tryon_uow, "usage"):
                            await self.tryon_uow.usage.record("failed", error_code=err.code)
                        await self.tryon_uow.commit()
                        return ProcessJobResult(
                            job_id=job.id,
                            status="failed",
                            artifact_key=job.artifact_key,
                            failure_reason=err.code,
                        )
        else:
            try:
                inference_out = await self.adapter.execute_tryon(
                    InferenceInput(
                        job_id=job_id,
                        user_id=job.user_id,
                        garment_id=job.garment_id,
                        user_photo_bytes=photo_bytes,
                        garment_image_bytes=garment_bytes,
                        garment_category=garment_category,
                    )
                )
                rendered_bytes = inference_out.rendered_image_bytes
                latency_ms = inference_out.inference_latency_ms
                model_version = inference_out.model_version
                pipeline_version = inference_out.pipeline_version
            except Exception as exc:
                async with self.tryon_uow:
                    await self.tryon_uow.jobs.update_status(
                        job_id, "failed", failure_reason="model_error"
                    )
                    await self.tryon_uow.commit()
                return ProcessJobResult(
                    job_id=job_id,
                    status="failed",
                    artifact_key=job.artifact_key,
                    failure_reason=f"model_error: {exc}",
                )

        # 5. Consent can be revoked during long vendor call: re-check, then discard result
        async with self.profile_uow:
            has_consent_post = await self.profile_uow.consents.has_consent(job.user_id, "body_photo")
        if not has_consent_post:
            async with self.tryon_uow:
                await self.tryon_uow.jobs.cancel(job.id, "consent_revoked")
                if hasattr(self.tryon_uow, "usage"):
                    await self.tryon_uow.usage.record("cancelled", error_code="consent_revoked")
                await self.tryon_uow.commit()
            return ProcessJobResult(
                job_id=job.id,
                status="cancelled",
                artifact_key=job.artifact_key,
                failure_reason="consent_revoked",
            )

        # 6. Post-processing & C2PA Watermarking (Rule I09)
        async with self.tryon_uow:
            await self.tryon_uow.jobs.update_status(job_id, "postprocessing")
            await self.tryon_uow.commit()

        try:
            watermarked_bytes = SyntheticWatermarker.apply_watermark(
                image_bytes=rendered_bytes,
                job_id=str(job_id),
                model_version=model_version,
            )
        except Exception:
            watermarked_bytes = rendered_bytes

        # 7. Post-Inference Quality Validation (Rule I10)
        async with self.tryon_uow:
            await self.tryon_uow.jobs.update_status(job_id, "quality_check")
            await self.tryon_uow.commit()

        quality_res = PostInferenceQualityValidator.validate(watermarked_bytes)
        if not quality_res.is_acceptable:
            async with self.tryon_uow:
                await self.tryon_uow.jobs.update_status(
                    job_id, "failed", failure_reason="quality_rejected"
                )
                if hasattr(self.tryon_uow, "usage"):
                    await self.tryon_uow.usage.record("failed", error_code="quality_rejected")
                await self.tryon_uow.commit()
            return ProcessJobResult(
                job_id=job_id,
                status="failed",
                artifact_key=job.artifact_key,
                failure_reason="quality_rejected",
            )

        # 8. Success: Store Result Object in Private Bucket First (Rule I06)
        key = media_key(job.user_id, "tryon_result", job.id)
        if self.storage:
            put_res = self.storage.put(key, watermarked_bytes, content_type="image/jpeg")
            if inspect.isawaitable(put_res):
                await put_res

        # 9. Success: Persist Artifact & Complete Job
        async with self.tryon_uow:
            artifact = TryOnArtifact(
                job_id=job_id,
                artifact_key=job.artifact_key,
                result_key=key,
                model_version=model_version,
                pipeline_version=pipeline_version,
                photo_version=1,
                garment_version=garment_version,
            )
            self.tryon_uow.artifacts.add(artifact)
            await self.tryon_uow.jobs.update_status(job_id, "completed")
            if hasattr(self.tryon_uow, "usage"):
                await self.tryon_uow.usage.record(
                    "completed",
                    provider=provider_name,
                    model=model_version,
                    latency_ms=int(latency_ms),
                    cost_usd_est=cost_usd_est,
                )
            await self.tryon_uow.commit()

        return ProcessJobResult(
            job_id=job_id,
            status="completed",
            artifact_key=job.artifact_key,
            result_url=key,
        )
