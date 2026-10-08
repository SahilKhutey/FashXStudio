from __future__ import annotations

"""Foundation 14 provider-backed VTO worker path.

The worker is provider-neutral and remains fail-closed when no commercial-approved
provider is configured.
"""

import json
from uuid import UUID

from fashx.profile.integrations.r2_client import R2StorageClient
from api.app.tryon.integrations.gpu_client import ConfiguredTryOnProvider
from api.app.tryon.integrations.media import ResultQualityError, TryOnExecutionGateway
from schemas.common.enums import TryOnFailureReason, TryOnStatus
from schemas.tryon.worker import TryOnWorkerComplete, TryOnWorkerFailure, TryOnWorkerProgress, TryOnWorkerResultQuality
from workers.tryon_gpu.api_client import TryOnInternalApiClient


async def claim_and_process(job_id: UUID) -> None:
    api = TryOnInternalApiClient()
    await api.claim(job_id)
    bundle = await api.prepare(job_id)
    storage = R2StorageClient()
    provider = ConfiguredTryOnProvider()
    gateway = TryOnExecutionGateway(storage=storage, provider=provider)

    try:
        await api.progress(job_id, TryOnWorkerProgress(status=TryOnStatus.PREPROCESSING))
        submission = await gateway.submit(
            job_id=UUID(bundle["job_id"]),
            photo_key=bundle["photo_key"],
            garment_key=bundle["garment_image_key"],
            model_version=bundle["model_version"],
            pipeline_version=bundle["pipeline_version"],
        )
        await api.provider_started(job_id, submission.provider_job_id)
        result = await provider.wait_for_result(provider_job_id=submission.provider_job_id)
        await api.progress(job_id, TryOnWorkerProgress(status=TryOnStatus.POSTPROCESSING))
        result_key = f"tryon-results/{bundle['artifact_key']}.jpg"
        _, quality = await gateway.fetch_result_to_r2(provider_result=result, result_key=result_key)
        await api.progress(job_id, TryOnWorkerProgress(status=TryOnStatus.QUALITY_CHECK))
        await api.complete(job_id, TryOnWorkerComplete(result_key=result_key, quality=TryOnWorkerResultQuality(quality_status="accepted", quality_score=quality.quality_score, width=quality.width, height=quality.height, size_bytes=quality.size_bytes, content_type=quality.content_type, content_sha256=quality.sha256, quality_reasons=list(quality.reasons))))
    except Exception as exc:
        message = str(exc).lower()
        reason = TryOnFailureReason.INTERNAL_ERROR
        if "timeout" in message:
            reason = TryOnFailureReason.TIMEOUT
        elif "disabled" in message or "provider" in message:
            reason = TryOnFailureReason.GPU_UNAVAILABLE
        elif isinstance(exc, ResultQualityError) or "quality validation" in message:
            reason = TryOnFailureReason.QUALITY_REJECTED
        elif "download" in message or "result" in message:
            reason = TryOnFailureReason.STORAGE_ERROR
        retryable = reason in {TryOnFailureReason.TIMEOUT, TryOnFailureReason.GPU_UNAVAILABLE, TryOnFailureReason.STORAGE_ERROR}
        await api.fail(job_id, TryOnWorkerFailure(reason=reason, retryable=retryable))


async def consume_once(payload: str) -> None:
    message = json.loads(payload)
    await claim_and_process(UUID(message["job_id"]))


if __name__ == "__main__":
    raise SystemExit("Run the worker under a queue supervisor with a configured provider.")
