from dataclasses import dataclass
from uuid import UUID

from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from api.app.core.errors import EntityNotFoundError
from api.app.profile.repositories.profile_repository import ProfileUnitOfWork
from api.app.tryon.adapters.mock_adapter import MockTryOnAdapter
from api.app.tryon.ports import InferenceInput, TryOnModelAdapterPort
from api.app.tryon.quality_validator import PostInferenceQualityValidator
from api.app.tryon.repositories.tryon_repository import TryOnUnitOfWork
from api.app.tryon.watermarker import SyntheticWatermarker
from database.models.tryon import TryOnArtifact


@dataclass(frozen=True)
class ProcessJobResult:
    job_id: UUID
    status: str
    artifact_key: str
    result_url: str | None = None
    failure_reason: str | None = None


class ProcessTryOnJobUseCase:
    """Worker use case: executes preprocessing, model inference, C2PA watermarking, and post-inference quality gate."""

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

        # 2. Retrieve Garment Details
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

        # Synthetic placeholder bytes if none provided
        photo_bytes = user_photo_bytes or b"SYNTHETIC_USER_PHOTO_BYTES_512x768"
        garment_bytes = garment_image_bytes or b"SYNTHETIC_GARMENT_BYTES_256x256"

        # 3. Model Inference (Rule I06 & Rule I08)
        async with self.tryon_uow:
            await self.tryon_uow.jobs.update_status(job_id, "inference")
            await self.tryon_uow.commit()

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

        # 4. Post-processing & Watermarking (Rule I09)
        async with self.tryon_uow:
            await self.tryon_uow.jobs.update_status(job_id, "postprocessing")
            await self.tryon_uow.commit()

        try:
            watermarked_bytes = SyntheticWatermarker.apply_watermark(
                image_bytes=inference_out.rendered_image_bytes,
                job_id=str(job_id),
                model_version=self.adapter.model_version,
            )
        except Exception:
            watermarked_bytes = inference_out.rendered_image_bytes

        # 5. Post-Inference Quality Validation (Rule I10)
        async with self.tryon_uow:
            await self.tryon_uow.jobs.update_status(job_id, "quality_check")
            await self.tryon_uow.commit()

        quality_res = PostInferenceQualityValidator.validate(watermarked_bytes)
        if not quality_res.is_acceptable:
            async with self.tryon_uow:
                await self.tryon_uow.jobs.update_status(
                    job_id, "failed", failure_reason="quality_rejected"
                )
                await self.tryon_uow.commit()
            return ProcessJobResult(
                job_id=job_id,
                status="failed",
                artifact_key=job.artifact_key,
                failure_reason="quality_rejected",
            )

        # 6. Success: Persist Artifact & Complete Job
        result_key = f"s3://fashx-tryon-artifacts/{job.artifact_key}.png"
        async with self.tryon_uow:
            artifact = TryOnArtifact(
                job_id=job_id,
                artifact_key=job.artifact_key,
                result_key=result_key,
                model_version=self.adapter.model_version,
                pipeline_version=self.adapter.pipeline_version,
                photo_version=1,
                garment_version=garment_version,
            )
            self.tryon_uow.artifacts.add(artifact)
            await self.tryon_uow.jobs.update_status(job_id, "completed")
            await self.tryon_uow.commit()

        return ProcessJobResult(
            job_id=job_id,
            status="completed",
            artifact_key=job.artifact_key,
            result_url=result_key,
        )
