"""FASHN Hosted Virtual Try-On API Adapter (tryon-v1.6 / Max)."""

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

log = logging.getLogger(__name__)

_PENDING = {"starting", "in_queue", "processing"}
MAX_RESULT_BYTES = 15 * 1024 * 1024


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
        client: httpx.Client | None = None,
        download_client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._model = model
        self._mode = mode
        self._cost = cost_usd_est
        self._sleep = sleep
        self._http = client or httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(20.0, connect=5.0),
        )
        # Dedicated client for downloading CDN outputs without Authorization header
        self._dl = download_client or httpx.Client(
            timeout=httpx.Timeout(30.0, connect=5.0)
        )

    # ---- error mapping -------------------------------------------------
    @staticmethod
    def _from_http(status: int, body: str) -> TryOnError:
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
        return str(data["id"])

    def collect(self, provider_job_id: str, *, deadline_s: float) -> TryOnOutput:
        t0 = time.monotonic()
        delay = 1.0

        while True:
            if time.monotonic() - t0 > deadline_s:
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
                return TryOnOutput(
                    image_bytes=img,
                    provider=self.provider,
                    model=self._model,
                    provider_job_id=provider_job_id,
                    latency_ms=int((time.monotonic() - t0) * 1000),
                    cost_usd_est=self._cost,
                )

            if st in _PENDING:
                self._sleep(delay + random.random() * 0.3)
                delay = min(delay * 1.4, 3.0)
                continue

            if st == "time_out":
                raise TryOnError(
                    "provider_timeout",
                    "Try-on took too long. We'll retry.",
                    retryable=True,
                    detail=provider_job_id,
                )

            # failed / canceled
            err = d.get("error") or {}
            name = (err.get("name") if isinstance(err, dict) else str(err)) or "unknown"
            log.warning("fashn failed job=%s error=%s", provider_job_id, name)
            raise TryOnError(
                f"provider_{name}".lower()[:60],
                "We couldn't fit this garment on that photo. Try another photo or garment.",
                retryable=False,
                detail=name,
            )

    def run(self, req: TryOnRequest, *, deadline_s: float = 90.0) -> TryOnOutput:
        return self.collect(self.submit(req), deadline_s=deadline_s)

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
            Image.open(io.BytesIO(r.content)).verify()
        except Exception as e:
            raise TryOnError(
                "provider_bad_image",
                "Try-on failed. We'll retry.",
                retryable=True,
                detail="undecodable result",
            ) from e

        return r.content
