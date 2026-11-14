from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

MIME_TO_FORMAT: dict[str, str] = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}

FORMAT_TO_MIME: dict[str, str] = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


@dataclass(frozen=True)
class ImageLimits:
    max_bytes: int
    max_width: int = 4096
    max_height: int = 4096
    max_pixels: int = 20_000_000


class InvalidImageError(ValueError):
    """Raised when an uploaded payload violates file format, dimension, or security constraints."""

    pass


def validate_and_normalize_image(
    raw: bytes,
    declared_mime: str,
    limits: ImageLimits,
) -> tuple[bytes, str, int, int]:
    """Validates uploaded raw image bytes, enforces security boundaries, strips EXIF, and normalizes to WebP.

    Returns:
        tuple of (normalized_webp_bytes, mime_type, width, height)
    """
    if not raw:
        raise InvalidImageError("Empty image payload")

    if len(raw) > limits.max_bytes:
        raise InvalidImageError(
            f"Image payload size ({len(raw)} bytes) exceeds limit ({limits.max_bytes} bytes)"
        )

    expected_format = MIME_TO_FORMAT.get(declared_mime.lower())
    if not expected_format:
        raise InvalidImageError(
            f"Unsupported declared MIME type: {declared_mime!r}"
        )

    try:
        with Image.open(BytesIO(raw)) as img:
            # Verify actual image header signature
            img.verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise InvalidImageError(f"Corrupted or invalid image data: {exc}") from exc

    # Re-open after verify() to inspect dimensions and normalize pixels
    try:
        with Image.open(BytesIO(raw)) as img:
            detected_format = img.format
            if detected_format not in FORMAT_TO_MIME:
                raise InvalidImageError(
                    f"Forbidden image format detected: {detected_format}"
                )

            # Prevent MIME spoofing (e.g., JPEG extension on PNG or non-matching format)
            if detected_format != expected_format:
                raise InvalidImageError(
                    f"MIME type mismatch: declared {declared_mime} but detected {detected_format}"
                )

            width, height = img.size
            if width <= 0 or height <= 0:
                raise InvalidImageError("Invalid image dimensions")

            if width > limits.max_width or height > limits.max_height:
                raise InvalidImageError(
                    f"Image dimensions {width}x{height} exceed maximum allowed {limits.max_width}x{limits.max_height}"
                )

            total_pixels = width * height
            if total_pixels > limits.max_pixels:
                raise InvalidImageError(
                    f"Total image pixel count ({total_pixels}) exceeds decompression bomb threshold ({limits.max_pixels})"
                )

            # Transpose orientation per EXIF tags if present, then strip all EXIF metadata
            transposed = ImageOps.exif_transpose(img)
            if transposed is None:
                transposed = img

            # Convert color mode: keep RGBA if transparency exists, otherwise RGB
            if transposed.mode in ("RGBA", "LA") or (
                transposed.mode == "P"
                and "transparency" in transposed.info  # type: ignore[attr-defined]
            ):
                normalized_img = transposed.convert("RGBA")
            else:
                normalized_img = transposed.convert("RGB")

            # Encode normalized image as WebP (stripping EXIF metadata for privacy)
            out = BytesIO()
            normalized_img.save(out, format="WEBP", quality=90, method=6)
            normalized_bytes = out.getvalue()

            return normalized_bytes, "image/webp", width, height

    except InvalidImageError:
        raise
    except Exception as exc:
        raise InvalidImageError(f"Failed to process and normalize image: {exc}") from exc
