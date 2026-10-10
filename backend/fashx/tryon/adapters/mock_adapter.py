import io
import time
from uuid import uuid4

from PIL import Image

from fashx.application.ports.tryon import TryOnOutput, TryOnRequest
from fashx.tryon.ports import InferenceInput, InferenceOutput


class MockTryOnAdapter:
    """Deterministic fast PIL-based compositing adapter for tests and local development."""

    provider = "mock"
    license_id = "mock"

    def __init__(
        self,
        model_version: str = "mock-vto-v1",
        pipeline_version: str = "pilot-pipe-v1",
    ) -> None:
        self._model_version = model_version
        self._pipeline_version = pipeline_version
        self._submitted_requests: dict[str, TryOnRequest] = {}
        self.submit_count: int = 0

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def pipeline_version(self) -> str:
        return self._pipeline_version

    @property
    def is_commercial_cleared(self) -> bool:
        return True

    def submit(self, req: TryOnRequest) -> str:
        self.submit_count += 1
        job_id = f"mock-job-{uuid4()}"
        self._submitted_requests[job_id] = req
        return job_id

    def collect(self, provider_job_id: str, *, deadline_s: float = 90.0) -> TryOnOutput:
        req = self._submitted_requests.get(provider_job_id)
        person_bytes = req.person_jpeg if req else b""
        garment_bytes = req.garment_jpeg if req else b""

        rendered = self._composite_bytes(person_bytes, garment_bytes)
        return TryOnOutput(
            image_bytes=rendered,
            provider=self.provider,
            model=self._model_version,
            provider_job_id=provider_job_id,
            latency_ms=10,
            cost_usd_est=0.0,
        )

    def run(self, req: TryOnRequest, *, deadline_s: float = 90.0) -> TryOnOutput:
        return self.collect(self.submit(req), deadline_s=deadline_s)

    def _composite_bytes(self, person_bytes: bytes, garment_bytes: bytes) -> bytes:
        try:
            user_img = Image.open(io.BytesIO(person_bytes)).convert("RGBA")
        except Exception:
            user_img = Image.new("RGBA", (512, 768), (180, 160, 150, 255))

        try:
            garment_img = Image.open(io.BytesIO(garment_bytes)).convert("RGBA")
        except Exception:
            garment_img = Image.new("RGBA", (256, 256), (30, 45, 90, 255))

        target_w = max(1, int(user_img.width * 0.6))
        target_h = max(1, int(user_img.height * 0.45))
        garment_resized = garment_img.resize((target_w, target_h), Image.Resampling.BILINEAR)

        pos_x = int((user_img.width - target_w) / 2)
        pos_y = int(user_img.height * 0.3)

        result_img = user_img.copy()
        result_img.paste(garment_resized, (pos_x, pos_y), garment_resized)

        out_buf = io.BytesIO()
        result_img.convert("RGB").save(out_buf, format="JPEG", quality=90)
        return out_buf.getvalue()

    async def execute_tryon(self, payload: InferenceInput) -> InferenceOutput:
        start_time = time.perf_counter()
        rendered_bytes = self._composite_bytes(
            payload.user_photo_bytes, payload.garment_image_bytes
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return InferenceOutput(
            rendered_image_bytes=rendered_bytes,
            model_version=self.model_version,
            pipeline_version=self.pipeline_version,
            inference_latency_ms=round(latency_ms, 2),
            raw_metadata={"category": payload.garment_category, "adapter": "MockTryOnAdapter"},
        )


MockAdapter = MockTryOnAdapter
