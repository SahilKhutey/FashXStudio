"""FASHN Hosted Virtual Try-On API Adapter (tryon-v1.6 / Max)."""

from __future__ import annotations

import asyncio
import io
import logging
import random
import time
from collections.abc import Callable
from urllib.parse import urlparse

import httpx
from PIL import Image

from fashx.application.ports.tryon import TryOnError, TryOnOutput, TryOnRequest
from fashx.core.metrics import emit_metric
from fashx.infrastructure.tryon.fashn_concurrency import FashnConcurrencyController
from fashx.infrastructure.tryon.fashn_errors import (
    map_fashn_http_error,
    map_fashn_status_error,
)
from fashx.infrastructure.tryon.fashn_health import (
    FashnHealthReport,
    check_fashn_health,
    log_provider_event,
)
from fashx.infrastructure.tryon.fashn_mapper import (
    FASHN_PENDING_STATUSES,
    build_fashn_run_payload,
    parse_fashn_status_response,
)
from fashx.tryon.ports import InferenceInput, InferenceOutput

log = logging.getLogger(__name__)

MAX_RESULT_BYTES = 15 * 1024 * 1024


def _normalize_result_image(
    data: bytes,
    *,
    max_bytes: int = MAX_RESULT_BYTES,
    max_pixels: int = 25_000_000,
    max_side: int = 4096,
) -> bytes:
    if not data or len(data) > max_bytes:
        raise ValueError("Provider result is empty or exceeds size limit")
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError("Unsupported provider image format")
            width, height = image.size
            if width < 256 or height < 256:
                raise ValueError("Provider result resolution is too small")
            if width * height > max_pixels:
                raise ValueError("Provider result exceeds pixel limit")
            image.load()
            image = image.convert("RGB")
            scale = min(1.0, max_side / max(image.size))
            if scale < 1.0:
                image = image.resize(
                    (
                        round(image.width * scale),
                        round(image.height * scale),
                    ),
                    Image.Resampling.LANCZOS,
                )
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=95)
            return output.getvalue()
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError(f"Unsupported or corrupt provider image: {exc}") from exc


class FashnApiAdapter:
    """Production commercial try-on adapter for the FASHN Hosted API."""

    provider = "fashn_api"
    license_id = "commercial-api"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.fashn.ai/v1",
        model: str = "tryon-v1.6",
        mode: str | None = None,
        *,
        cost_usd_est: float | None = 0.075,
        cost_per_credit_usd: float = 0.075,
        timeout_s: float = 90.0,
        connect_timeout_seconds: float = 5.0,
        request_timeout_seconds: float = 30.0,
        read_timeout_seconds: float = 15.0,
        status_max_retries: int = 3,
        poll_interval_seconds: float = 3.0,
        max_concurrent_predictions: int = 2,
        max_submissions_per_minute: int = 10,
        client: httpx.Client | None = None,
        download_client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        environment: str = "dev",
    ) -> None:
        self._model = model
        self._mode = mode
        self._cost = cost_usd_est
        self._cost_per_credit = cost_per_credit_usd
        self._timeout_s = timeout_s
        self._sleep = sleep
        self._env = environment
        self._status_max_retries = max(0, status_max_retries)
        self._poll_interval_s = max(0.5, poll_interval_seconds)

        self._concurrency = FashnConcurrencyController(
            max_concurrent=max_concurrent_predictions,
            max_submissions_per_minute=max_submissions_per_minute,
        )

        if client is not None and "Authorization" not in client.headers:
            client.headers["Authorization"] = f"Bearer {api_key}"
        self._http = client or httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(
                request_timeout_seconds,
                connect=connect_timeout_seconds,
                read=read_timeout_seconds,
            ),
        )
        # Dedicated client for downloading CDN outputs without Authorization header
        self._dl = download_client or httpx.Client(
            timeout=httpx.Timeout(
                request_timeout_seconds,
                connect=connect_timeout_seconds,
                read=read_timeout_seconds,
            )
        )

    @property
    def timeout_s(self) -> float:
        return self._timeout_s

    @property
    def model_version(self) -> str:
        return self._model

    @property
    def pipeline_version(self) -> str:
        return "fashn-hosted-v1"

    @property
    def is_commercial_cleared(self) -> bool:
        return True

    def check_health(self) -> FashnHealthReport:
        """Probe provider API connectivity and account balance."""
        return check_fashn_health(self._http, model=self._model)

    # ---- error mapping convenience -------------------------------------
    def _from_http(self, status: int, body: str) -> TryOnError:
        return map_fashn_http_error(
            status,
            body,
            environment=self._env,
            provider=self.provider,
            model=self._model,
        )

    # ---- two-phase API -------------------------------------------------
    def submit(self, req: TryOnRequest) -> str:
        # 1. Enforce submission rate limits
        self._concurrency.acquire_submission_slot()

        # 2. Build payload
        payload = build_fashn_run_payload(
            req,
            model=self._model,
            mode=self._mode,
        )

        log_provider_event(
            "tryon.provider.submit.started",
            {
                "provider": self.provider,
                "model": self._model,
                "category": req.category,
                "environment": self._env,
            },
        )

        # 3. Submit prediction (submit_max_retries = 0: no blind retries on network error)
        try:
            r = self._http.post("/run", json=payload)
        except httpx.TransportError as e:
            log_provider_event(
                "tryon.provider.submit.error",
                {"error": type(e).__name__, "environment": self._env},
                level=logging.ERROR,
            )
            raise TryOnError(
                "provider_unreachable",
                "Try-on is busy. We'll retry shortly.",
                retryable=True,
                detail=type(e).__name__,
            ) from e

        if r.status_code >= 400:
            raise self._from_http(r.status_code, r.text)

        data = r.json()
        if data.get("error") or not data.get("id"):
            err_msg = str(data.get("error"))[:200]
            log_provider_event(
                "tryon.provider.submit.rejected",
                {"error": err_msg, "environment": self._env},
                level=logging.WARNING,
            )
            raise TryOnError(
                "bad_input",
                "We couldn't use this photo or garment. Try another photo.",
                retryable=False,
                detail=err_msg,
            )

        job_id = str(data["id"])

        # 4. Acquire active prediction concurrency slot
        try:
            self._concurrency.acquire_prediction_slot()
        except TryOnError:
            # Concurrency limit reached; caller will retry
            log.warning("FASHN active concurrency cap reached after job submission: %s", job_id)

        log_provider_event(
            "tryon.provider.submit.accepted",
            {
                "provider": self.provider,
                "model": self._model,
                "provider_job_id": job_id,
                "environment": self._env,
            },
        )
        emit_metric(
            "VTOJobSubmitted",
            1.0,
            unit="Count",
            service="tryon",
            environment=self._env,
            dimensions={"Provider": self.provider, "ModelVersion": self._model},
            namespace="FashX/VTO",
        )
        return job_id

    def collect(self, provider_job_id: str, *, deadline_s: float) -> TryOnOutput:
        t0 = time.monotonic()
        delay = self._poll_interval_s
        consecutive_poll_errors = 0

        try:
            while True:
                if time.monotonic() - t0 > deadline_s:
                    emit_metric(
                        "VTOProviderTimeout",
                        1.0,
                        unit="Count",
                        service="tryon",
                        environment=self._env,
                        dimensions={"Provider": self.provider, "ModelVersion": self._model},
                        namespace="FashX/VTO",
                    )
                    emit_metric(
                        "VTOJobFailed",
                        1.0,
                        unit="Count",
                        service="tryon",
                        environment=self._env,
                        dimensions={"Provider": self.provider, "ModelVersion": self._model, "Outcome": "timeout"},
                        namespace="FashX/VTO",
                    )
                    log_provider_event(
                        "tryon.provider.timeout",
                        {
                            "provider": self.provider,
                            "model": self._model,
                            "provider_job_id": provider_job_id,
                            "elapsed_s": round(time.monotonic() - t0, 2),
                        },
                        level=logging.ERROR,
                    )
                    raise TryOnError(
                        "provider_timeout",
                        "Try-on took too long. We'll retry.",
                        retryable=True,
                        detail=provider_job_id,
                    )

                # Poll status with transient network retry
                try:
                    r = self._http.get(f"/status/{provider_job_id}")
                    consecutive_poll_errors = 0
                except httpx.TransportError as e:
                    consecutive_poll_errors += 1
                    if consecutive_poll_errors <= self._status_max_retries:
                        log.warning(
                            "Transient transport error polling %s (attempt %d/%d): %s",
                            provider_job_id,
                            consecutive_poll_errors,
                            self._status_max_retries,
                            e,
                        )
                        self._sleep(min(delay * 1.5, 5.0))
                        continue
                    raise TryOnError(
                        "provider_unreachable",
                        "Try-on is busy. We'll retry shortly.",
                        retryable=True,
                        detail=type(e).__name__,
                    ) from e

                if r.status_code >= 400:
                    raise self._from_http(r.status_code, r.text)

                data = r.json()
                status_result = parse_fashn_status_response(data, headers=dict(r.headers))

                # Handle successful completion
                if status_result.is_success:
                    url = status_result.output_urls[0] if status_result.output_urls else None
                    if not url:
                        raise TryOnError(
                            "provider_empty",
                            "Try-on failed. We'll retry.",
                            retryable=True,
                            detail="completed without output",
                        )
                    img = self._download(url)
                    latency_ms = int((time.monotonic() - t0) * 1000)
                    credits_used = status_result.credits_used or 1.0
                    cost_usd = (
                        round(credits_used * self._cost_per_credit, 4)
                        if self._cost_per_credit
                        else self._cost
                    )

                    emit_metric(
                        "VTOJobSucceeded",
                        1.0,
                        unit="Count",
                        service="tryon",
                        environment=self._env,
                        dimensions={"Provider": self.provider, "ModelVersion": self._model, "Outcome": "success"},
                        namespace="FashX/VTO",
                    )
                    emit_metric(
                        "VTOProviderLatency",
                        float(latency_ms),
                        unit="Milliseconds",
                        service="tryon",
                        environment=self._env,
                        dimensions={"Provider": self.provider, "ModelVersion": self._model},
                        namespace="FashX/VTO",
                    )
                    if cost_usd is not None:
                        emit_metric(
                            "VTOProviderCostEstimate",
                            float(cost_usd),
                            unit="None",
                            service="tryon",
                            environment=self._env,
                            dimensions={"Provider": self.provider, "ModelVersion": self._model},
                            namespace="FashX/VTO",
                        )
                    emit_metric(
                        "VTOProviderCreditsUsed",
                        float(credits_used),
                        unit="Count",
                        service="tryon",
                        environment=self._env,
                        dimensions={"Provider": self.provider, "ModelVersion": self._model},
                        namespace="FashX/VTO",
                    )
                    log_provider_event(
                        "tryon.provider.completed",
                        {
                            "provider": self.provider,
                            "model": self._model,
                            "provider_job_id": provider_job_id,
                            "latency_ms": latency_ms,
                            "credits_used": credits_used,
                            "cost_usd": cost_usd,
                        },
                    )
                    return TryOnOutput(
                        image_bytes=img,
                        provider=self.provider,
                        model=self._model,
                        provider_job_id=provider_job_id,
                        latency_ms=latency_ms,
                        cost_usd_est=cost_usd,
                        credits_used=credits_used,
                    )

                # Still processing
                if status_result.status in FASHN_PENDING_STATUSES:
                    self._sleep(delay + random.random() * 0.3)
                    delay = min(delay * 1.4, 4.0)
                    continue

                # Timed out by provider
                if status_result.status == "time_out":
                    emit_metric(
                        "VTOProviderTimeout",
                        1.0,
                        unit="Count",
                        service="tryon",
                        environment=self._env,
                        dimensions={"Provider": self.provider, "ModelVersion": self._model},
                        namespace="FashX/VTO",
                    )
                    emit_metric(
                        "VTOJobFailed",
                        1.0,
                        unit="Count",
                        service="tryon",
                        environment=self._env,
                        dimensions={"Provider": self.provider, "ModelVersion": self._model, "Outcome": "timeout"},
                        namespace="FashX/VTO",
                    )
                    raise TryOnError(
                        "provider_timeout",
                        "Try-on took too long. We'll retry.",
                        retryable=True,
                        detail=provider_job_id,
                    )

                # Failed or cancelled
                if status_result.status in {"failed", "canceled", "cancelled"}:
                    log_provider_event(
                        "tryon.provider.failed",
                        {
                            "provider": self.provider,
                            "model": self._model,
                            "provider_job_id": provider_job_id,
                            "error_name": status_result.error_name,
                            "error_message": status_result.error_message,
                        },
                        level=logging.WARNING,
                    )
                    raise map_fashn_status_error(
                        status_result.error_name,
                        status_result.error_message,
                        environment=self._env,
                        provider=self.provider,
                        model=self._model,
                    )

                # Unexpected provider status
                raise TryOnError(
                    "provider_invalid_status",
                    "Try-on is temporarily unavailable.",
                    retryable=False,
                    detail=f"Unexpected provider status: {str(status_result.status)[:60]}",
                )
        finally:
            self._concurrency.release_prediction_slot()

    def run(self, req: TryOnRequest, *, deadline_s: float = 90.0) -> TryOnOutput:
        return self.collect(self.submit(req), deadline_s=deadline_s)

    async def execute_tryon(self, payload: InferenceInput) -> InferenceOutput:
        category = (
            payload.garment_category
            if payload.garment_category in ("tops", "bottoms", "one-pieces")
            else "auto"
        )
        req = TryOnRequest(
            person_jpeg=payload.user_photo_bytes,
            garment_jpeg=payload.garment_image_bytes,
            category=category,
        )
        # httpx.Client and the polling/sleep logic are synchronous.
        # Run them outside the application's event loop.
        out = await asyncio.to_thread(
            self.run,
            req,
            deadline_s=self._timeout_s,
        )
        return InferenceOutput(
            rendered_image_bytes=out.image_bytes,
            model_version=self.model_version,
            pipeline_version=self.pipeline_version,
            inference_latency_ms=float(out.latency_ms),
            raw_metadata={
                "category": payload.garment_category,
                "provider": self.provider,
                "provider_job_id": out.provider_job_id,
                "cost_usd_est": out.cost_usd_est,
                "credits_used": getattr(out, "credits_used", 1.0),
            },
        )

    def _download(self, url: str) -> bytes:
        u = urlparse(url)
        # SSRF guard: verify https scheme and domain ending with .fashn.ai
        if u.scheme != "https" or not (u.hostname or "").endswith(".fashn.ai"):
            raise TryOnError(
                "provider_bad_url",
                "Try-on failed. We'll retry.",
                retryable=True,
                detail=u.hostname or "",
            )

        try:
            r = self._dl.get(url)
        except httpx.TransportError as e:
            raise TryOnError(
                "provider_unreachable",
                "Try-on is busy. We'll retry shortly.",
                retryable=True,
                detail=type(e).__name__,
            ) from e

        if r.status_code != 200 or len(r.content) > MAX_RESULT_BYTES:
            raise TryOnError(
                "provider_download",
                "Try-on failed. We'll retry.",
                retryable=True,
                detail=f"http {r.status_code}",
            )

        try:
            return _normalize_result_image(r.content)
        except ValueError as exc:
            emit_metric(
                "VTOResultValidationFailure",
                1.0,
                unit="Count",
                service="tryon",
                environment=self._env,
                dimensions={"Provider": self.provider, "ModelVersion": self._model},
                namespace="FashX/VTO",
            )
            emit_metric(
                "VTOJobFailed",
                1.0,
                unit="Count",
                service="tryon",
                environment=self._env,
                dimensions={"Provider": self.provider, "ModelVersion": self._model, "Outcome": "validation_failure"},
                namespace="FashX/VTO",
            )
            raise TryOnError(
                "provider_bad_image",
                "Try-on returned an invalid image. Please retry.",
                retryable=False,
                detail=str(exc),
            ) from exc
