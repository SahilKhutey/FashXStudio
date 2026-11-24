import asyncio
import inspect
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from database.models.tryon import TryOnArtifact
from fashx.application.ports.tryon import TryOnError, TryOnRequest
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import EntityNotFoundError
from fashx.ml.prep import prepare_for_provider
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.tryon.artifact_metadata import inspect_artifact
from fashx.tryon.domain.state_machine import ProviderAttemptStatus
from fashx.tryon.output_validation import validate_provider_output
from fashx.tryon.ports import InferenceInput
from fashx.tryon.quality_validator import PostInferenceQualityValidator
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork
from fashx.tryon.watermarker import SyntheticWatermarker

log = logging.getLogger(__name__)


async def _run_maybe_thread(func: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        asyncio.get_running_loop()
        return await asyncio.to_thread(func, *args, **kwargs)
    except RuntimeError:
        return func(*args, **kwargs)


def _validate_image_bytes(data: bytes | None, label: str) -> None:
    if not data or len(data) < 16:
        raise ValueError(f"Validated {label} bytes are required and cannot be empty")
    from io import BytesIO

    from PIL import Image

    try:
        with Image.open(BytesIO(data)) as im:
            im.verify()
    except Exception as exc:
        raise ValueError(f"Undecodable or corrupt {label} bytes: {exc}") from exc


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
        validation_service: Any | None = None,
    ) -> None:
        self.tryon_uow = tryon_uow
        self.profile_uow = profile_uow
        self.catalog_uow = catalog_uow
        self.validation_service = validation_service
        if adapter is not None:
            self.adapter = adapter
        else:
            from fashx.core.dependencies import get_tryon_adapter

            self.adapter = get_tryon_adapter()
        if storage is not None:
            self.storage = storage
        else:
            try:
                from fashx.core.dependencies import get_storage

                self.storage = get_storage()
            except Exception:
                self.storage = None
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

        # 3. Retrieve Garment Details and recheck current source clearance and try-on rights
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

            # Recheck live source clearance and try-on rights at job execution time
            if hasattr(self.catalog_uow, "merchant_products") and hasattr(
                self.catalog_uow.merchant_products, "get_by_canonical_garment_id"
            ):
                products = await self.catalog_uow.merchant_products.get_by_canonical_garment_id(
                    garment.id
                )
                if products:
                    for prod in products:
                        if prod.source_id and hasattr(self.catalog_uow, "sources"):
                            src = await self.catalog_uow.sources.get_by_id(prod.source_id)
                            if src and (
                                src.status != "cleared"
                                or not src.rights_display
                                or not src.rights_tryon
                            ):
                                async with self.tryon_uow:
                                    await self.tryon_uow.jobs.update_status(
                                        job_id, "failed", failure_reason="tryon_rights_revoked"
                                    )
                                    await self.tryon_uow.commit()
                                return ProcessJobResult(
                                    job_id=job_id,
                                    status="failed",
                                    artifact_key=job.artifact_key,
                                    failure_reason="tryon_rights_revoked",
                                )

            garment_id = garment.id
            garment_category = garment.category

        # Resolve storage
        storage = self.storage
        if storage is None:
            try:
                from fashx.core.dependencies import get_storage

                storage = get_storage()
            except Exception:
                storage = None

        photo_bytes = user_photo_bytes
        if photo_bytes is None:
            photo_err = None
            photo_storage_key = None
            async with self.profile_uow:
                photo = None
                if getattr(job, "profile_photo_id", None):
                    photo = await self.profile_uow.photos.get_by_id(job.profile_photo_id)
                if photo is None:
                    photo = await self.profile_uow.photos.get_active_photo(
                        job.user_id, "tryon_reference"
                    )

                if photo is None:
                    photo_err = "missing_photo"
                elif photo.user_id != job.user_id:
                    photo_err = "unauthorized_photo"
                elif getattr(photo, "status", None) != "accepted":
                    photo_err = "photo_not_accepted"
                elif not getattr(photo, "storage_key", None):
                    photo_err = "missing_photo_bytes"
                else:
                    photo_storage_key = photo.storage_key

            if photo_err:
                async with self.tryon_uow:
                    await self.tryon_uow.jobs.update_status(
                        job_id, "failed", failure_reason=photo_err
                    )
                    await self.tryon_uow.commit()
                return ProcessJobResult(
                    job_id=job_id,
                    status="failed",
                    artifact_key=job.artifact_key,
                    failure_reason=photo_err,
                )

            if not photo_storage_key or storage is None:
                async with self.tryon_uow:
                    await self.tryon_uow.jobs.update_status(
                        job_id, "failed", failure_reason="missing_photo_bytes"
                    )
                    await self.tryon_uow.commit()
                return ProcessJobResult(
                    job_id=job_id,
                    status="failed",
                    artifact_key=job.artifact_key,
                    failure_reason="missing_photo_bytes",
                )

            try:
                res = storage.get(photo_storage_key)
                if inspect.isawaitable(res):
                    res = await res
                photo_bytes = res
            except Exception:
                photo_bytes = None

            if not photo_bytes:
                async with self.tryon_uow:
                    await self.tryon_uow.jobs.update_status(
                        job_id, "failed", failure_reason="missing_photo_bytes"
                    )
                    await self.tryon_uow.commit()
                return ProcessJobResult(
                    job_id=job_id,
                    status="failed",
                    artifact_key=job.artifact_key,
                    failure_reason="missing_photo_bytes",
                )

        garment_bytes = garment_image_bytes
        if garment_bytes is None:
            garment_storage_key = None
            async with self.catalog_uow:
                if hasattr(self.catalog_uow, "images"):
                    images = await self.catalog_uow.images.list_for_garment(garment_id)
                    target_img = None
                    for img in images:
                        if getattr(img, "image_type", None) == "primary":
                            target_img = img
                            break
                    if not target_img and images:
                        target_img = images[0]
                    if target_img:
                        garment_storage_key = getattr(target_img, "storage_key", None)

            if not garment_storage_key or storage is None:
                async with self.tryon_uow:
                    await self.tryon_uow.jobs.update_status(
                        job_id, "failed", failure_reason="missing_garment_image_bytes"
                    )
                    await self.tryon_uow.commit()
                return ProcessJobResult(
                    job_id=job_id,
                    status="failed",
                    artifact_key=job.artifact_key,
                    failure_reason="missing_garment_image_bytes",
                )

            try:
                res = storage.get(garment_storage_key)
                if inspect.isawaitable(res):
                    res = await res
                garment_bytes = res
            except Exception:
                garment_bytes = None

            if not garment_bytes:
                async with self.tryon_uow:
                    await self.tryon_uow.jobs.update_status(
                        job_id, "failed", failure_reason="missing_garment_image_bytes"
                    )
                    await self.tryon_uow.commit()
                return ProcessJobResult(
                    job_id=job_id,
                    status="failed",
                    artifact_key=job.artifact_key,
                    failure_reason="missing_garment_image_bytes",
                )

        # Validate that image inputs are decodable and non-corrupt
        try:
            _validate_image_bytes(photo_bytes, "person photo")
        except ValueError as exc:
            async with self.tryon_uow:
                await self.tryon_uow.jobs.update_status(
                    job_id, "failed", failure_reason="invalid_photo_bytes"
                )
                await self.tryon_uow.commit()
            return ProcessJobResult(
                job_id=job_id,
                status="failed",
                artifact_key=job.artifact_key,
                failure_reason=f"invalid_photo_bytes: {exc}",
            )

        try:
            _validate_image_bytes(garment_bytes, "garment image")
        except ValueError as exc:
            async with self.tryon_uow:
                await self.tryon_uow.jobs.update_status(
                    job_id, "failed", failure_reason="invalid_garment_image_bytes"
                )
                await self.tryon_uow.commit()
            return ProcessJobResult(
                job_id=job_id,
                status="failed",
                artifact_key=job.artifact_key,
                failure_reason=f"invalid_garment_image_bytes: {exc}",
            )

        # Mandatory Phase 07.3 Input Validation Gate
        if self.validation_service is not None:
            photo_asset_id = getattr(job, "profile_photo_id", None) or job.user_id
            from fashx.tryon.validation.contracts import ValidationRequest

            val_req = ValidationRequest(
                user_id=job.user_id,
                shopper_asset_id=photo_asset_id,
                product_id=job.garment_id,
                garment_category=garment_category,
            )
            val_result = await self.validation_service.validate_and_record(
                job_id=job.id, request=val_req
            )
            if not val_result.can_submit:
                issue = (
                    val_result.shopper.issues[0]
                    if val_result.shopper.issues
                    else (val_result.garment.issues[0] if val_result.garment.issues else None)
                )
                err_code = issue.code if issue else "validation_rejected"
                user_msg = issue.user_message if issue else "Input validation failed."
                async with self.tryon_uow:
                    await self.tryon_uow.jobs.fail(job.id, err_code, user_msg)
                    if hasattr(self.tryon_uow, "usage"):
                        await self.tryon_uow.usage.record("failed", error_code=err_code)
                    await self.tryon_uow.commit()
                return ProcessJobResult(
                    job_id=job.id,
                    status="failed",
                    artifact_key=job.artifact_key,
                    failure_reason=err_code,
                )

        # Pre-inference consent revalidation (Time-of-use recheck)
        async with self.profile_uow:
            has_consent_before_inference = await self.profile_uow.consents.has_consent(
                job.user_id, "body_photo"
            )
        if not has_consent_before_inference:
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

        # 4. Model Inference with Circuit Breaker and Provider Attempts (Rule 7.4.15 - 7.4.18)
        async with self.tryon_uow:
            await self.tryon_uow.jobs.update_status(job_id, "submitting")
            job_cur = await self.tryon_uow.jobs.get_by_id(job_id)
            if job_cur and hasattr(job_cur, "progress_stage"):
                job_cur.progress_stage = "submitting_to_provider"
            await self.tryon_uow.commit()

        cost_usd_est: float | None = 0.0
        provider_name = getattr(self.adapter, "provider", "fashn_api")
        model_version = getattr(self.adapter, "model_version", "tryon-v1.6")
        pipeline_version = getattr(self.adapter, "pipeline_version", "pilot-pipe-v1")
        latency_ms = 0.0
        attempt_record = None

        if hasattr(self.adapter, "submit") and hasattr(self.adapter, "collect"):
            try:
                if self.breaker:
                    self.breaker.guard()

                deadline_s = float(
                    getattr(self.adapter, "timeout_s", getattr(self.adapter, "_timeout_s", 90.0))
                )
                provider_job_id = getattr(job, "provider_job_id", None)
                if not provider_job_id:
                    cat_arg = (
                        garment_category
                        if garment_category in ("tops", "bottoms", "one-pieces")
                        else "auto"
                    )
                    req = TryOnRequest(
                        person_jpeg=prepare_for_provider(photo_bytes),
                        garment_jpeg=prepare_for_provider(garment_bytes),
                        category=cat_arg,
                    )

                    # Persist provider attempt before POST (Rule 7.4.16)
                    async with self.tryon_uow:
                        if hasattr(self.tryon_uow, "provider_attempts"):
                            existing_attempts = await self.tryon_uow.provider_attempts.get_by_job_id(job.id)
                            att_num = len(existing_attempts) + 1
                            attempt_record = await self.tryon_uow.provider_attempts.create_attempt(
                                job_id=job.id,
                                attempt_number=att_num,
                                provider=provider_name,
                                model_version=model_version,
                                status=ProviderAttemptStatus.SUBMITTING.value,
                                request_hash=getattr(job, "request_hash", None) or "unhashed",
                            )
                            attempt_record.submitted_at = datetime.now(UTC)
                        await self.tryon_uow.commit()

                    try:
                        if inspect.iscoroutinefunction(self.adapter.submit):
                            provider_job_id = await self.adapter.submit(req)
                        else:
                            provider_job_id = await _run_maybe_thread(self.adapter.submit, req)
                    except Exception as submit_exc:
                        # Ambiguous submission: record UNKNOWN and SUBMISSION_UNKNOWN (Rule 7.4.16)
                        async with self.tryon_uow:
                            if attempt_record and hasattr(self.tryon_uow, "provider_attempts"):
                                await self.tryon_uow.provider_attempts.update_status(
                                    attempt_record.id,
                                    status=ProviderAttemptStatus.UNKNOWN.value,
                                    safe_error_detail=str(submit_exc),
                                )
                            await self.tryon_uow.jobs.update_status(
                                job.id, "submission_unknown", failure_reason="submission_timeout"
                            )
                            job_up = await self.tryon_uow.jobs.get_by_id(job.id)
                            if job_up and hasattr(job_up, "progress_stage"):
                                job_up.progress_stage = "submission_unknown"
                            await self.tryon_uow.commit()

                        return ProcessJobResult(
                            job_id=job.id,
                            status="submission_unknown",
                            artifact_key=job.artifact_key,
                            failure_reason=f"submission_unknown: {submit_exc}",
                        )

                    # Persist provider job ID immediately upon acceptance (Rule 7.4.17)
                    async with self.tryon_uow:
                        await self.tryon_uow.jobs.set_provider_job(
                            job.id, provider_name, provider_job_id
                        )
                        job_up = await self.tryon_uow.jobs.get_by_id(job.id)
                        if job_up:
                            job_up.provider_job_id = provider_job_id
                            job_up.provider = provider_name
                            job_up.provider_submitted_at = datetime.now(UTC)
                            job_up.status = "submitted"
                            if hasattr(job_up, "progress_stage"):
                                job_up.progress_stage = "provider_inference"
                        if attempt_record and hasattr(self.tryon_uow, "provider_attempts"):
                            await self.tryon_uow.provider_attempts.update_status(
                                attempt_record.id,
                                status=ProviderAttemptStatus.ACCEPTED.value,
                                provider_job_id=provider_job_id,
                            )
                        await self.tryon_uow.commit()

                if inspect.iscoroutinefunction(self.adapter.collect):
                    out = await self.adapter.collect(provider_job_id, deadline_s=deadline_s)
                else:
                    out = await _run_maybe_thread(
                        self.adapter.collect, provider_job_id, deadline_s=deadline_s
                    )
                if self.breaker:
                    self.breaker.success()

                rendered_bytes = out.image_bytes
                latency_ms = float(out.latency_ms)
                cost_usd_est = out.cost_usd_est
                model_version = out.model
                provider_name = out.provider

                if attempt_record and hasattr(self.tryon_uow, "provider_attempts"):
                    async with self.tryon_uow:
                        await self.tryon_uow.provider_attempts.update_status(
                            attempt_record.id,
                            status=ProviderAttemptStatus.COMPLETED.value,
                            completed_at=datetime.now(UTC),
                        )
                        await self.tryon_uow.commit()

            except TryOnError as err:
                if err.code in ("provider_unavailable", "provider_unreachable", "provider_timeout"):
                    if self.breaker:
                        self.breaker.failure()

                if attempt_record and hasattr(self.tryon_uow, "provider_attempts"):
                    async with self.tryon_uow:
                        await self.tryon_uow.provider_attempts.update_status(
                            attempt_record.id,
                            status=ProviderAttemptStatus.FAILED.value,
                            provider_error_code=err.code,
                            safe_error_detail=err.user_message or str(err),
                            completed_at=datetime.now(UTC),
                        )
                        await self.tryon_uow.commit()

                max_attempts = 3
                attempts = getattr(job, "attempts", 1)
                async with self.tryon_uow:
                    if err.retryable and (err.code == "breaker_open" or attempts < max_attempts):
                        await self.tryon_uow.jobs.requeue(
                            job.id,
                            delay_s=min(2**attempts * 5, 120),
                            clear_provider_job=False if provider_job_id else True,
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

        # 5. Check if job was deleted (e.g. photo was deleted mid-flight) or consent was revoked
        async with self.tryon_uow:
            current_job = await self.tryon_uow.jobs.get_by_id(job_id)
        if current_job is None:
            return ProcessJobResult(
                job_id=job_id,
                status="cancelled",
                artifact_key=job.artifact_key,
                failure_reason="job_deleted",
            )

        async with self.profile_uow:
            has_consent_post = await self.profile_uow.consents.has_consent(
                job.user_id, "body_photo"
            )
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

        # 6. Provider Output Image Validation (Rule 7.4.20)
        async with self.tryon_uow:
            await self.tryon_uow.jobs.update_status(job_id, "validating_output")
            job_val = await self.tryon_uow.jobs.get_by_id(job_id)
            if job_val and hasattr(job_val, "progress_stage"):
                job_val.progress_stage = "validating_output"
            await self.tryon_uow.commit()

        try:
            val_out = validate_provider_output(rendered_bytes)
            rendered_bytes = val_out.data
        except ValueError as val_err:
            log.warning("Output validation failed for job %s: %s", job_id, val_err)
            async with self.tryon_uow:
                await self.tryon_uow.jobs.update_status(
                    job_id, "failed", failure_reason="output_validation_failed"
                )
                if hasattr(self.tryon_uow, "usage"):
                    await self.tryon_uow.usage.record("failed", error_code="output_validation_failed")
                await self.tryon_uow.commit()
            return ProcessJobResult(
                job_id=job_id,
                status="failed",
                artifact_key=job.artifact_key,
                failure_reason="output_validation_failed",
            )

        # 7. Post-Inference Quality Validation on provider output (Rule I10)
        async with self.tryon_uow:
            await self.tryon_uow.jobs.update_status(job_id, "quality_check")
            await self.tryon_uow.commit()

        quality_res = PostInferenceQualityValidator.validate(rendered_bytes)
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

        # 7. Post-processing & C2PA Watermarking (Rule I09)
        async with self.tryon_uow:
            await self.tryon_uow.jobs.update_status(job_id, "postprocessing")
            await self.tryon_uow.commit()

        try:
            watermarked_bytes = SyntheticWatermarker.apply_watermark(
                image_bytes=rendered_bytes,
                job_id=str(job_id),
                model_version=model_version,
            )
        except Exception as exc:
            log.warning("Watermarking failed for job %s: %s", job_id, exc)
            async with self.tryon_uow:
                await self.tryon_uow.jobs.update_status(
                    job_id,
                    "failed",
                    failure_reason="watermark_failed",
                )
                if hasattr(self.tryon_uow, "usage"):
                    await self.tryon_uow.usage.record(
                        "failed",
                        error_code="watermark_failed",
                    )
                await self.tryon_uow.commit()
            return ProcessJobResult(
                job_id=job_id,
                status="failed",
                artifact_key=job.artifact_key,
                failure_reason="watermark_failed",
            )

        # 8. Artifact Metadata Inspection (Phase 6)
        try:
            metadata = inspect_artifact(watermarked_bytes)
        except (ValueError, OSError) as meta_exc:
            log.warning("Artifact metadata inspection failed for job %s: %s", job_id, meta_exc)
            async with self.tryon_uow:
                await self.tryon_uow.jobs.update_status(
                    job_id, "failed", failure_reason="artifact_invalid"
                )
                if hasattr(self.tryon_uow, "usage"):
                    await self.tryon_uow.usage.record("failed", error_code="artifact_invalid")
                await self.tryon_uow.commit()
            return ProcessJobResult(
                job_id=job_id,
                status="failed",
                artifact_key=job.artifact_key,
                failure_reason="artifact_invalid",
            )

        # 9. Verify job still exists and is not cancelled before storing result in bucket
        async with self.tryon_uow:
            final_check = await self.tryon_uow.jobs.get_by_id(job_id)
            if final_check is None or getattr(final_check, "cancel_requested", False):
                await self.tryon_uow.jobs.cancel(job_id, "cancel_requested")
                if hasattr(self.tryon_uow, "usage"):
                    await self.tryon_uow.usage.record("cancelled", error_code="cancel_requested")
                await self.tryon_uow.commit()
                return ProcessJobResult(
                    job_id=job_id,
                    status="cancelled",
                    artifact_key=job.artifact_key,
                    failure_reason="cancel_requested",
                )

        # The watermarker currently outputs PNG. Keep key and MIME type consistent.
        key = f"u/{job.user_id}/tryon/{job.id}{metadata.extension}"
        stored = False
        try:
            if self.storage is None:
                raise RuntimeError("Private object storage is not configured")

            put_res = self.storage.put(
                key,
                watermarked_bytes,
                content_type=metadata.content_type,
            )
            if inspect.isawaitable(put_res):
                await put_res
            stored = True

            # Consent is checked again after the upload and before DB publication.
            async with self.profile_uow:
                has_consent_final = await self.profile_uow.consents.has_consent(
                    job.user_id, "body_photo"
                )
            if not has_consent_final:
                raise PermissionError("consent_revoked")

            async with self.tryon_uow:
                job_record = await self.tryon_uow.jobs.get_by_id(job_id)
                if job_record is None or getattr(job_record, "cancel_requested", False):
                    raise RuntimeError("job_cancelled_or_deleted")

                quality_reasons_list: list[str] = []
                if quality_res.failure_reason:
                    quality_reasons_list.append(quality_res.failure_reason)
                if quality_res.diagnostics:
                    quality_reasons_list.extend(str(k) for k in quality_res.diagnostics.keys())

                artifact = TryOnArtifact(
                    job_id=job_id,
                    artifact_key=job.artifact_key,
                    result_key=key,
                    model_version=model_version,
                    pipeline_version=pipeline_version,
                    photo_version=getattr(job, "photo_version", 1),
                    garment_version=getattr(job, "garment_version", 1),
                    quality_status="accepted",
                    quality_score=quality_res.structural_score,
                    width=metadata.width,
                    height=metadata.height,
                    size_bytes=metadata.size_bytes,
                    content_type=metadata.content_type,
                    content_sha256=metadata.content_sha256,
                    quality_reasons=quality_reasons_list,
                    provider=provider_name,
                    provider_model_version=model_version,
                    output_sha256=metadata.content_sha256,
                    processing_latency_ms=int(latency_ms),
                )
                self.tryon_uow.artifacts.add(artifact)
                await self.tryon_uow.jobs.update_status(job_id, "completed")
                if job_record:
                    job_record.progress_stage = "completed"
                    job_record.provider_completed_at = datetime.now(UTC)
                if hasattr(self.tryon_uow, "usage"):
                    await self.tryon_uow.usage.record(
                        "completed",
                        provider=provider_name,
                        model=model_version,
                        latency_ms=int(latency_ms),
                        cost_usd_est=cost_usd_est,
                    )
                await self.tryon_uow.commit()

        except PermissionError:
            log.info("Consent revoked for job %s during/after upload", job_id)
            if stored and self.storage and hasattr(self.storage, "delete"):
                try:
                    del_res = self.storage.delete(key)
                    if inspect.isawaitable(del_res):
                        await del_res
                except Exception as del_exc:
                    log.warning("Storage cleanup failed for %s: %s", key, del_exc)
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
        except RuntimeError as rt_exc:
            reason = str(rt_exc)
            if stored and self.storage and hasattr(self.storage, "delete"):
                try:
                    del_res = self.storage.delete(key)
                    if inspect.isawaitable(del_res):
                        await del_res
                except Exception as del_exc:
                    log.warning("Storage cleanup failed for %s: %s", key, del_exc)
            if reason == "job_cancelled_or_deleted":
                async with self.tryon_uow:
                    await self.tryon_uow.jobs.cancel(job_id, "cancel_requested")
                    if hasattr(self.tryon_uow, "usage"):
                        await self.tryon_uow.usage.record(
                            "cancelled", error_code="cancel_requested"
                        )
                    await self.tryon_uow.commit()
                return ProcessJobResult(
                    job_id=job_id,
                    status="cancelled",
                    artifact_key=job.artifact_key,
                    failure_reason="cancel_requested",
                )
            async with self.tryon_uow:
                await self.tryon_uow.jobs.update_status(
                    job_id, "failed", failure_reason="storage_error"
                )
                if hasattr(self.tryon_uow, "usage"):
                    await self.tryon_uow.usage.record("failed", error_code="storage_error")
                await self.tryon_uow.commit()
            return ProcessJobResult(
                job_id=job_id,
                status="failed",
                artifact_key=job.artifact_key,
                failure_reason="storage_error",
            )
        except Exception as exc:
            log.warning("Storage upload or DB commit failed for job %s: %s", job_id, exc)
            if stored and self.storage and hasattr(self.storage, "delete"):
                try:
                    del_res = self.storage.delete(key)
                    if inspect.isawaitable(del_res):
                        await del_res
                except Exception as del_exc:
                    log.warning("Storage cleanup failed for %s: %s", key, del_exc)
            async with self.tryon_uow:
                await self.tryon_uow.jobs.update_status(
                    job_id, "failed", failure_reason="storage_error"
                )
                if hasattr(self.tryon_uow, "usage"):
                    await self.tryon_uow.usage.record("failed", error_code="storage_error")
                await self.tryon_uow.commit()
            return ProcessJobResult(
                job_id=job_id,
                status="failed",
                artifact_key=job.artifact_key,
                failure_reason="storage_error",
            )

        return ProcessJobResult(
            job_id=job_id,
            status="completed",
            artifact_key=job.artifact_key,
            result_url=key,
        )
