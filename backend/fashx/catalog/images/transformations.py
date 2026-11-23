"""Generation of optimized display derivatives and VTO-compatible garment inputs."""

from __future__ import annotations

import io

from PIL import Image

from fashx.catalog.images.hasher import ImageHasher
from fashx.catalog.images.models import GeneratedDerivative, InspectedImage, TransformationType

DISPLAY_PROFILES: dict[TransformationType, dict] = {
    TransformationType.DISPLAY_THUMBNAIL: {
        "max_w": 384,
        "max_h": 384,
        "quality": 80,
        "format": "WEBP",
        "mime": "image/webp",
    },
    TransformationType.DISPLAY_CARD: {
        "max_w": 768,
        "max_h": 768,
        "quality": 82,
        "format": "WEBP",
        "mime": "image/webp",
    },
    TransformationType.DISPLAY_DETAIL: {
        "max_w": 1200,
        "max_h": 1200,
        "quality": 85,
        "format": "WEBP",
        "mime": "image/webp",
    },
}


class ImageTransformationService:
    """Generates display and VTO derivatives from normalized image bytes."""

    PROCESSOR_NAME = "fashx-pillow-transformer"
    PROCESSOR_VERSION = "v1"

    @classmethod
    def _fit_dimensions(cls, width: int, height: int, max_w: int, max_h: int) -> tuple[int, int]:
        """Scale dimensions preserving aspect ratio."""
        if width <= max_w and height <= max_h:
            return width, height
        scale = min(max_w / max(width, 1), max_h / max(height, 1))
        return max(1, int(width * scale)), max(1, int(height * scale))

    @classmethod
    def generate_display_derivative(
        cls,
        inspected: InspectedImage,
        transformation_type: TransformationType,
        version: str = "v1",
    ) -> GeneratedDerivative:
        """Create a WebP display derivative (thumbnail, card, or detail)."""
        cfg = DISPLAY_PROFILES.get(
            transformation_type,
            DISPLAY_PROFILES[TransformationType.DISPLAY_CARD],
        )

        with Image.open(io.BytesIO(inspected.normalized_bytes)) as img:
            orig_w, orig_h = img.size
            new_w, new_h = cls._fit_dimensions(orig_w, orig_h, cfg["max_w"], cfg["max_h"])

            # Handle transparency: paste on pure white background for WebP
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                bg = Image.new("RGB", (orig_w, orig_h), (255, 255, 255))
                rgba = img.convert("RGBA")
                bg.paste(rgba, mask=rgba.split()[3])
                img = bg
            elif img.mode != "RGB":
                img = img.convert("RGB")

            resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            buf = io.BytesIO()
            resized.save(buf, format=cfg["format"], quality=cfg["quality"], method=6)
            data = buf.getvalue()
            sha256 = ImageHasher.compute_sha256(data)

            return GeneratedDerivative(
                transformation_type=transformation_type,
                version=version,
                processor_name=cls.PROCESSOR_NAME,
                processor_version=cls.PROCESSOR_VERSION,
                data=data,
                format=cfg["format"],
                mime_type=cfg["mime"],
                width=new_w,
                height=new_h,
                byte_size=len(data),
                sha256=sha256,
            )

    @classmethod
    def generate_vto_input(
        cls,
        inspected: InspectedImage,
        version: str = "v1",
        max_dim: int = 1024,
    ) -> GeneratedDerivative:
        """Generate high-fidelity, garment-preserving PNG derivative for VTO processors."""
        with Image.open(io.BytesIO(inspected.normalized_bytes)) as img:
            orig_w, orig_h = img.size
            new_w, new_h = cls._fit_dimensions(orig_w, orig_h, max_dim, max_dim)

            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")

            resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            buf = io.BytesIO()
            resized.save(buf, format="PNG", optimize=True)
            data = buf.getvalue()
            sha256 = ImageHasher.compute_sha256(data)

            return GeneratedDerivative(
                transformation_type=TransformationType.VTO_INPUT,
                version=version,
                processor_name="fashx-vto-preprocessor",
                processor_version="v1",
                data=data,
                format="PNG",
                mime_type="image/png",
                width=new_w,
                height=new_h,
                byte_size=len(data),
                sha256=sha256,
            )
