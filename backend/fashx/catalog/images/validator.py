"""Byte-level image content validation and format verification using Pillow."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB
MAX_IMAGE_PIXELS = 20_000_000      # 20 Megapixels
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


@dataclass(frozen=True)
class ValidatedImage:
    """Decoded and verified image metadata and content."""

    content: bytes
    image_format: str
    width: int
    height: int


def validate_image_bytes(content: bytes) -> ValidatedImage:
    """Validate raw image bytes against format, byte size, decompression bombs, and pixel limits."""
    if not content:
        raise ValueError("Image is empty")
    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError(f"Image exceeds byte limit of {MAX_IMAGE_BYTES} bytes")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as image:
                image_format = (image.format or "").upper()
                if image_format not in ALLOWED_FORMATS:
                    raise ValueError(f"Unsupported image format: '{image_format}'. Must be one of {ALLOWED_FORMATS}")

                width, height = image.size
                if width * height > MAX_IMAGE_PIXELS:
                    raise ValueError(f"Image exceeds pixel limit of {MAX_IMAGE_PIXELS} pixels (got {width * height})")

                return ValidatedImage(
                    content=content,
                    image_format=image_format,
                    width=width,
                    height=height,
                )
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f"Malformed or unrecognized image content: {exc}") from exc
