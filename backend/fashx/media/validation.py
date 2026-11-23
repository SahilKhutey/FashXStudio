from __future__ import annotations

import hashlib
import io
import warnings
from dataclasses import dataclass
from typing import Final

from PIL import (
    Image,
    ImageFile,
    ImageOps,
    UnidentifiedImageError,
)
from PIL.Image import DecompressionBombError

from .errors import ImageValidationError

# Ensure Pillow never loads truncated images silently
ImageFile.LOAD_TRUNCATED_IMAGES = False

# Hard ceiling on decompressed pixels to prevent zip/decompression bombs (Rule 4.5.3)
MAX_PIXELS: Final[int] = 20_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS

MIN_FILE_BYTES: Final[int] = 10 * 1024          # 10 KB
MAX_FILE_BYTES: Final[int] = 10 * 1024 * 1024   # 10 MB
MAX_WIDTH: Final[int] = 4096
MAX_HEIGHT: Final[int] = 4096

ALLOWED_FORMATS: Final[dict[str, str]] = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


@dataclass(frozen=True)
class ValidatedImage:
    original_sha256: str
    normalized_sha256: str
    original_size_bytes: int
    normalized_size_bytes: int
    width: int
    height: int
    detected_format: str
    output_content_type: str
    normalized_bytes: bytes


def detect_magic_format(data: bytes) -> str | None:
    """Inspect leading magic bytes to identify container format before full decode."""
    if len(data) < 12:
        return None
    if data[:3] == b"\xff\xd8\xff":
        return "JPEG"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "PNG"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "WEBP"
    return None


def validate_declared_mime(
    declared_content_type: str | None,
    detected_format: str,
) -> None:
    """Ensure client's declared Content-Type matches the verified container format."""
    expected = ALLOWED_FORMATS.get(detected_format)
    if expected is None:
        raise ImageValidationError("unsupported_image_format")

    if declared_content_type:
        declared = declared_content_type.split(";")[0].strip().lower()
        # Accept image/jpg as alias for image/jpeg
        if declared == "image/jpg":
            declared = "image/jpeg"
        if declared != expected:
            raise ImageValidationError("image_content_type_mismatch")


def validate_dimensions(width: int, height: int) -> None:
    """Enforce image dimensions and pixel count limits."""
    if width <= 0 or height <= 0:
        raise ImageValidationError("image_dimensions_exceeded")
    if width > MAX_WIDTH or height > MAX_HEIGHT:
        raise ImageValidationError("image_dimensions_exceeded")
    if width * height > MAX_PIXELS:
        raise ImageValidationError("image_dimensions_exceeded")


def validate_image(
    raw_bytes: bytes,
    declared_content_type: str | None = None,
) -> ValidatedImage:
    """
    Safely inspect, decode, validate and normalize personal user images.

    1. Checks file size bounds (10 KB to 10 MB).
    2. Inspects magic bytes for supported format.
    3. Verifies declared MIME consistency.
    4. Decodes image with Pillow under strict resource boundaries.
    5. Rejects multi-frame / animated images.
    6. Validates width, height, and pixel counts.
    7. Strips all EXIF/GPS/device metadata and normalizes orientation.
    8. Generates a fresh, verified raster output (WebP).
    """
    original_size = len(raw_bytes)
    if original_size < MIN_FILE_BYTES:
        raise ImageValidationError("image_size_below_minimum")
    if original_size > MAX_FILE_BYTES:
        raise ImageValidationError("image_size_exceeded")

    # 1. Magic bytes identification
    magic_format = detect_magic_format(raw_bytes)
    if magic_format is None:
        raise ImageValidationError("unsupported_image_format")

    # 2. Declared MIME check
    validate_declared_mime(declared_content_type, magic_format)

    # 3. Decode image
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", DecompressionBombError)
            img = Image.open(io.BytesIO(raw_bytes))
            actual_format = (img.format or "").upper()
            if actual_format not in ALLOWED_FORMATS:
                raise ImageValidationError("unsupported_image_format")

            # Reject animated or multi-frame images
            if getattr(img, "is_animated", False) or getattr(img, "n_frames", 1) > 1:
                raise ImageValidationError("animated_image_unsupported")

            # Force complete decode of all image pixels to detect corruption or truncation
            img.load()

            # Verify dimensions
            width, height = img.size
            validate_dimensions(width, height)

            # Normalization: handle EXIF orientation
            try:
                oriented_img = ImageOps.exif_transpose(img)
                if oriented_img is not None:
                    img = oriented_img
            except Exception:
                # If exif transpose fails, proceed with original raster
                pass

            # Convert color mode safely (strip alpha unless required, or normalize RGBA)
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                normalized_mode = "RGBA"
                out_format = "WEBP"
                out_mime = "image/webp"
            elif img.mode in ("RGB", "L"):
                normalized_mode = "RGB" if img.mode == "RGB" else "RGB"
                out_format = "WEBP"
                out_mime = "image/webp"
            elif img.mode == "CMYK":
                img = img.convert("RGB")
                normalized_mode = "RGB"
                out_format = "WEBP"
                out_mime = "image/webp"
            else:
                img = img.convert("RGB")
                normalized_mode = "RGB"
                out_format = "WEBP"
                out_mime = "image/webp"

            if img.mode != normalized_mode:
                img = img.convert(normalized_mode)

            # Re-check oriented dimensions
            norm_width, norm_height = img.size
            validate_dimensions(norm_width, norm_height)

            # Save to fresh buffer without original metadata (EXIF/GPS stripped)
            out_buf = io.BytesIO()
            img.save(
                out_buf,
                format=out_format,
                quality=90,
                method=6,
            )
            normalized_bytes = out_buf.getvalue()

            if not normalized_bytes:
                raise ImageValidationError("image_decode_failed")

    except ImageValidationError:
        raise
    except DecompressionBombError:
        raise ImageValidationError("image_dimensions_exceeded")
    except UnidentifiedImageError:
        raise ImageValidationError("image_decode_failed")
    except Exception as exc:
        raise ImageValidationError("image_decode_failed", message=f"Image decoding failed: {exc}") from exc

    orig_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    norm_sha256 = hashlib.sha256(normalized_bytes).hexdigest()

    return ValidatedImage(
        original_sha256=orig_sha256,
        normalized_sha256=norm_sha256,
        original_size_bytes=original_size,
        normalized_size_bytes=len(normalized_bytes),
        width=norm_width,
        height=norm_height,
        detected_format=actual_format,
        output_content_type=out_mime,
        normalized_bytes=normalized_bytes,
    )
