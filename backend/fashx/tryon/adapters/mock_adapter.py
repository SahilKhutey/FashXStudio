import io
import time

from fashx.tryon.ports import InferenceInput, InferenceOutput
from PIL import Image


class MockTryOnAdapter:
    """Deterministic fast PIL-based compositing adapter for tests and local development."""

    def __init__(
        self,
        model_version: str = "mock-vto-v1",
        pipeline_version: str = "pilot-pipe-v1",
    ) -> None:
        self._model_version = model_version
        self._pipeline_version = pipeline_version

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def pipeline_version(self) -> str:
        return self._pipeline_version

    @property
    def is_commercial_cleared(self) -> bool:
        return True

    async def execute_tryon(self, payload: InferenceInput) -> InferenceOutput:
        start_time = time.perf_counter()

        # Load user photo and garment image
        try:
            user_img = Image.open(io.BytesIO(payload.user_photo_bytes)).convert("RGBA")
        except Exception:
            user_img = Image.new("RGBA", (512, 768), (180, 160, 150, 255))

        try:
            garment_img = Image.open(io.BytesIO(payload.garment_image_bytes)).convert("RGBA")
        except Exception:
            garment_img = Image.new("RGBA", (256, 256), (30, 45, 90, 255))

        # Scale garment to fit torso area (middle 50% width, 40% height)
        target_w = int(user_img.width * 0.6)
        target_h = int(user_img.height * 0.45)
        garment_resized = garment_img.resize((target_w, target_h), Image.Resampling.BILINEAR)

        # Composite garment onto torso position
        pos_x = int((user_img.width - target_w) / 2)
        pos_y = int(user_img.height * 0.3)

        result_img = user_img.copy()
        result_img.paste(garment_resized, (pos_x, pos_y), garment_resized)

        # Export to PNG bytes
        out_buf = io.BytesIO()
        result_img.convert("RGB").save(out_buf, format="PNG")
        rendered_bytes = out_buf.getvalue()

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return InferenceOutput(
            rendered_image_bytes=rendered_bytes,
            model_version=self.model_version,
            pipeline_version=self.pipeline_version,
            inference_latency_ms=round(latency_ms, 2),
            raw_metadata={"category": payload.garment_category, "adapter": "MockTryOnAdapter"},
        )
