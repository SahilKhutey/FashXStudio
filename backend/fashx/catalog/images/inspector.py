"""Multi-layer byte inspection, format verification, and decode safety."""

from __future__ import annotations

import io
import warnings
from typing import Any

from PIL import Image, ImageFile, ImageOps, UnidentifiedImageError

from fashx.catalog.images.hasher import ImageHasher
from fashx.catalog.images.models import InspectedImage

# Enforce strict Pillow decoding standards
Image.MAX_IMAGE_PIXELS = 20_000_000  # 20 Megapixels
ImageFile.LOAD_TRUNCATED_IMAGES = False

MIN_DIMENSION = 400
MAX_DIMENSION = 4096
MAX_PIXELS = 20_000_000
MAX_BYTES = 10 * 1024 * 1024

SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}
MIME_BY_FORMAT = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


class ImageInspectionError(Exception):
    """Raised when raw image bytes fail format, dimension, or decode safety checks."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


class ImageInspector:
    """Performs deep byte validation, signature checking, dimension bounding, and EXIF normalization."""

    @classmethod
    def check_magic_bytes(cls, raw: bytes) -> str:
        """Inspect file signature / magic numbers."""
        if not raw or len(raw) < 12:
            raise ImageInspectionError("corrupted_image", "Image bytes are too short or empty")

        if raw.startswith(b"\xff\xd8\xff"):
            return "JPEG"
        if raw.startswith(b"\x89PNG\r\n\x1a\n"):
            return "PNG"
        if raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
            return "WEBP"

        # Check for prohibited signatures
        if raw.startswith(b"GIF87a") or raw.startswith(b"GIF89a"):
            raise ImageInspectionError("prohibited_format", "Animated GIF is not permitted")
        if b"<svg" in raw[:1024].lower() or b"<?xml" in raw[:1024].lower():
            raise ImageInspectionError("prohibited_format", "SVG format is prohibited")
        if raw.startswith(b"%PDF"):
            raise ImageInspectionError("prohibited_format", "PDF document is prohibited")
        if raw.startswith(b"<!DOCTYPE") or raw.startswith(b"<html") or raw.startswith(b"<HTML"):
            raise ImageInspectionError(
                "html_payload", "HTML response received instead of image bytes"
            )

        raise ImageInspectionError(
            "unsupported_mime", "Unsupported or unrecognized image signature"
        )

    @classmethod
    def inspect(cls, raw: bytes) -> InspectedImage:
        """Inspect and validate image bytes, verifying format, dimensions, orientation, and safety."""
        if not raw or len(raw) > MAX_BYTES:
            raise ImageInspectionError(
                "invalid_size", f"Image size exceeds maximum limit of {MAX_BYTES} bytes"
            )

        magic_fmt = cls.check_magic_bytes(raw)
        original_sha256 = ImageHasher.compute_sha256(raw)

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                buffer = io.BytesIO(raw)
                with Image.open(buffer) as img:
                    detected_format = (img.format or magic_fmt).upper()
                    if detected_format == "JPG":
                        detected_format = "JPEG"

                    if detected_format not in SUPPORTED_FORMATS:
                        raise ImageInspectionError(
                            "unsupported_format",
                            f"Detected image format '{detected_format}' is not supported",
                        )

                    # Reject animated images under initial policy
                    is_animated = bool(getattr(img, "is_animated", False))
                    if is_animated or getattr(img, "n_frames", 1) > 1:
                        raise ImageInspectionError(
                            "animated_image_rejected",
                            "Animated images (multi-frame) are not permitted",
                        )

                    width, height = img.size
                    if width <= 0 or height <= 0:
                        raise ImageInspectionError(
                            "invalid_dimensions", "Image dimensions must be positive"
                        )
                    if width < MIN_DIMENSION or height < MIN_DIMENSION:
                        raise ImageInspectionError(
                            "image_too_small",
                            f"Image dimensions ({width}x{height}) below minimum required {MIN_DIMENSION}x{MIN_DIMENSION}",
                        )
                    if width > MAX_DIMENSION or height > MAX_DIMENSION:
                        raise ImageInspectionError(
                            "image_dimensions_exceeded",
                            f"Image dimensions ({width}x{height}) exceed maximum allowed {MAX_DIMENSION}x{MAX_DIMENSION}",
                        )
                    if width * height > MAX_PIXELS:
                        raise ImageInspectionError(
                            "image_pixel_limit_exceeded",
                            f"Image pixel count ({width * height}) exceeds maximum limit of {MAX_PIXELS}",
                        )

                    # Apply EXIF transposition for correct orientation
                    transposed = ImageOps.exif_transpose(img)
                    final_w, final_h = transposed.size

                    # Compute perceptual dHash
                    perceptual_hash = ImageHasher.compute_dhash(transposed)

                    # Strip EXIF and normalize to clean bytes
                    norm_buf = io.BytesIO()
                    save_format = detected_format
                    save_kwargs: dict[str, Any] = {}
                    if save_format == "JPEG":
                        if transposed.mode != "RGB":
                            transposed = transposed.convert("RGB")
                        save_kwargs = {"quality": 92, "optimize": True}
                    elif save_format == "PNG":
                        save_kwargs = {"optimize": True}
                    elif save_format == "WEBP":
                        save_kwargs = {"quality": 90, "lossless": False}

                    transposed.save(norm_buf, format=save_format, **save_kwargs)
                    normalized_bytes = norm_buf.getvalue()
                    normalized_sha256 = ImageHasher.compute_sha256(normalized_bytes)

                    return InspectedImage(
                        original_bytes=raw,
                        original_sha256=original_sha256,
                        normalized_bytes=normalized_bytes,
                        normalized_sha256=normalized_sha256,
                        detected_format=detected_format,
                        mime_type=MIME_BY_FORMAT.get(detected_format, "image/jpeg"),
                        width=final_w,
                        height=final_h,
                        byte_size=len(raw),
                        perceptual_hash=perceptual_hash,
                        is_animated=False,
                    )

        except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
            raise ImageInspectionError(
                "decompression_bomb", f"Decompression bomb detected: {exc}"
            ) from exc
        except UnidentifiedImageError as exc:
            raise ImageInspectionError("corrupted_image", f"Cannot decode image: {exc}") from exc
        except (OSError, SyntaxError) as exc:
            raise ImageInspectionError("corrupted_image", f"Corrupted image stream: {exc}") from exc
