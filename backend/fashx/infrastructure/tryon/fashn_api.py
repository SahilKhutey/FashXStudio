"""FASHN Hosted Virtual Try-On API Adapter (tryon-v1.6 / Max)."""

import asyncio
import base64
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
from fashx.tryon.ports import InferenceInput, InferenceOutput

log = logging.getLogger(__name__)

_PENDING = {"starting", "in_queue", "processing"}
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


def _b64(jpeg: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()


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
        timeout_s: float = 90.0,
        client: httpx.Client | None = None,
        download_client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        environment: str = "dev",
    ) -> None:
        self._model = model
        self._mode = mode
        self._cost = cost_usd_est
        self._timeout_s = timeout_s
        self._sleep = sleep
        self._env = environment
        if client is not None and "Authorization" not in client.headers:
            client.headers["Authorization"] = f"Bearer {api_key}"
        self._http = client or httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(20.0, connect=5.0),
        )
        # Dedicated client for downloading CDN outputs without Authorization header
        self._dl = download_client or httpx.Client(timeout=httpx.Timeout(30.0, connect=5.0))

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

    # ---- error mapping -------------------------------------------------
    def _from_http(self, status: int, body: str) -> TryOnError:
        if status == 429:
            emit_metric(
                "VTOProviderRateLimit",
                1.0,
                unit="Count",
                service="tryon",
                environment=self._env,
                dimensions={"Provider": self.provider, "ModelVersion": self._model},
                namespace="FashX/VTO",
            )
        elif status in (401, 403):
            emit_metric(
                "VTOProviderAuthFailure",
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
            dimensions={"Provider": self.provider, "ModelVersion": self._model, "Outcome": f"http_{status}"},
            namespace="FashX/VTO",
        )
        if status in (429, 500, 502, 503, 504):
            return TryOnError(
                "provider_unavailable",
                "Try-on is busy. We'll retry shortly.",
                retryable=True,
                detail=f"http {status}",
            )
        if status in (401, 403):
            return TryOnError(
                "provider_auth",
                "Try-on is temporarily unavailable.",
                retryable=False,
                detail="auth rejected (check key)",
            )
        if status == 402:
            return TryOnError(
                "provider_credits",
                "Try-on is temporarily unavailable.",
                retryable=False,
                detail="credits exhausted",
            )
        return TryOnError(
            "bad_input",
            "We couldn't use this photo or garment. Try another photo.",
            retryable=False,
            detail=f"http {status}: {body[:200]}",
        )

    # ---- two-phase API -------------------------------------------------
    def submit(self, req: TryOnRequest) -> str:
        inputs = {
            "model_image": _b64(req.person_jpeg),
            "garment_image": _b64(req.garment_jpeg),
            "category": req.category,
        }
        if self._mode:
            inputs["mode"] = self._mode

        try:
            r = self._http.post(
                "/run",
                json={"model_name": self._model, "inputs": inputs},
            )
        except httpx.TransportError as e:
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
            raise TryOnError(
                "bad_input",
                "We couldn't use this photo or garment. Try another photo.",
                retryable=False,
                detail=str(data.get("error"))[:200],
            )
        job_id = str(data["id"])
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
        delay = 1.0

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
                raise TryOnError(
                    "provider_timeout",
                    "Try-on took too long. We'll retry.",
                    retryable=True,
                    detail=provider_job_id,
                )

            try:
                r = self._http.get(f"/status/{provider_job_id}")
            except httpx.TransportError as e:
                raise TryOnError(
                    "provider_unreachable",
                    "Try-on is busy. We'll retry shortly.",
                    retryable=True,
                    detail=type(e).__name__,
                ) from e

            if r.status_code >= 400:
                raise self._from_http(r.status_code, r.text)

            d = r.json()
            st = d.get("status")

            if st == "completed":
                url = (d.get("output") or [None])[0]
                if not url:
                    raise TryOnError(
                        "provider_empty",
                        "Try-on failed. We'll retry.",
                        retryable=True,
                        detail="completed without output",
                    )
                img = self._download(url)
                latency_ms = int((time.monotonic() - t0) * 1000)
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
                if self._cost is not None:
                    emit_metric(
                        "VTOProviderCostEstimate",
                        float(self._cost),
                        unit="None",
                        service="tryon",
                        environment=self._env,
                        dimensions={"Provider": self.provider, "ModelVersion": self._model},
                        namespace="FashX/VTO",
                    )
                return TryOnOutput(
                    image_bytes=img,
                    provider=self.provider,
                    model=self._model,
                    provider_job_id=provider_job_id,
                    latency_ms=latency_ms,
                    cost_usd_est=self._cost,
                )

            if st in _PENDING:
                self._sleep(delay + random.random() * 0.3)
                delay = min(delay * 1.4, 3.0)
                continue

            if st == "time_out":
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

            if st in {"failed", "canceled", "cancelled"}:
                err = d.get("error") or {}
                name = (err.get("name") if isinstance(err, dict) else str(err)) or "unknown"
                log.warning("fashn failed job=%s error=%s", provider_job_id, name)
                emit_metric(
                    "VTOJobFailed",
                    1.0,
                    unit="Count",
                    service="tryon",
                    environment=self._env,
                    dimensions={"Provider": self.provider, "ModelVersion": self._model, "Outcome": "provider_failed"},
                    namespace="FashX/VTO",
                )
                raise TryOnError(
                    "provider_failed",
                    "We couldn't generate this try-on. Try another photo or garment.",
                    retryable=False,
                    detail=str(name)[:160],
                )

            raise TryOnError(
                "provider_invalid_status",
                "Try-on is temporarily unavailable.",
                retryable=False,
                detail=f"Unexpected provider status: {str(st)[:60]}",
            )

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
                "Try-on is busy. We'll retry.",
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
