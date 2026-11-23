from __future__ import annotations

import warnings
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError


class PreprocessingError(ValueError):
    """Raised when image preprocessing fails due to corrupt, invalid, or out-of-bounds data."""


@dataclass(frozen=True)
class PreprocessingConfig:
    """Configuration parameters for fashion image preprocessing."""

    target_size: tuple[int, int] = (224, 224)
    min_dimension: int = 100
    max_dimension: int = 4096
    max_aspect_ratio: float = 4.0
    fill_color: tuple[int, int, int] = (255, 255, 255)


def preprocess_image(
    image_bytes: bytes,
    config: PreprocessingConfig | None = None,
) -> Image.Image:
    """Transform raw image bytes into a normalized, aspect-ratio preserved, square RGB image.

    Steps:
    1. Verify non-empty bytes and decode image.
    2. Enforce dimension bounds (min 100px, max 4096px).
    3. Enforce maximum aspect ratio limit (default 4.0).
    4. Normalize EXIF orientation transpose and strip EXIF metadata.
    5. Convert to 3-channel sRGB, blending transparency over white background.
    6. Uniformly scale preserving aspect ratio using Bicubic interpolation.
    7. Center onto a target square canvas with neutral background padding.
    """
    if not image_bytes:
        raise PreprocessingError("Image bytes are empty")

    cfg = config or PreprocessingConfig()

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            img = Image.open(BytesIO(image_bytes))
            img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombWarning) as exc:
        raise PreprocessingError(f"Failed to decode image bytes: {exc}") from exc

    # 1. EXIF orientation correction
    try:
        img = ImageOps.exif_transpose(img) or img
    except Exception:
        # Fallback if EXIF data is unparseable
        pass

    # 2. Dimension bounds check
    w, h = img.size
    if w < cfg.min_dimension or h < cfg.min_dimension:
        raise PreprocessingError(
            f"Image dimensions ({w}x{h}) below minimum allowed ({cfg.min_dimension}x{cfg.min_dimension})"
        )
    if w > cfg.max_dimension or h > cfg.max_dimension:
        raise PreprocessingError(
            f"Image dimensions ({w}x{h}) exceed maximum allowed ({cfg.max_dimension}x{cfg.max_dimension})"
        )

    # 3. Aspect ratio check
    aspect_ratio = max(w / h, h / w)
    if aspect_ratio > cfg.max_aspect_ratio:
        raise PreprocessingError(
            f"Image aspect ratio {aspect_ratio:.2f} exceeds maximum allowed {cfg.max_aspect_ratio:.2f}"
        )

    # 4. Color space normalization to RGB
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba_img = img.convert("RGBA")
        background = Image.new("RGBA", rgba_img.size, (*cfg.fill_color, 255))
        alpha_composite = Image.alpha_composite(background, rgba_img)
        rgb_img = alpha_composite.convert("RGB")
    elif img.mode != "RGB":
        rgb_img = img.convert("RGB")
    else:
        rgb_img = img

    # 5. Aspect-ratio preserving resize with centering and neutral padding
    target_w, target_h = cfg.target_size
    scale = min(target_w / w, target_h / h)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    resized = rgb_img.resize((new_w, new_h), resample=Image.Resampling.BICUBIC)

    canvas = Image.new("RGB", cfg.target_size, cfg.fill_color)
    offset_x = (target_w - new_w) // 2
    offset_y = (target_h - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y))

    return canvas


def preprocess_image_bytes(
    image_bytes: bytes,
    config: PreprocessingConfig | None = None,
    output_format: str = "JPEG",
    quality: int = 90,
) -> bytes:
    """Convenience helper returning preprocessed image bytes."""
    canvas = preprocess_image(image_bytes, config)
    out_buf = BytesIO()
    canvas.save(out_buf, format=output_format, quality=quality)
    return out_buf.getvalue()


__all__ = [
    "PreprocessingConfig",
    "PreprocessingError",
    "preprocess_image",
    "preprocess_image_bytes",
]
