"""Unit tests for server-side image validation and normalization to WebP."""

from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from fashx.infrastructure.storage.image_validation import (
    ImageLimits,
    InvalidImageError,
    validate_and_normalize_image,
)


def make_image(image_format: str = "JPEG", size: tuple[int, int] = (100, 100), color: str = "white") -> bytes:
    output = BytesIO()
    mode = "RGBA" if image_format.upper() == "PNG" else "RGB"
    img = Image.new(mode, size, color)
    img.save(output, format=image_format)
    return output.getvalue()


def test_accepts_valid_jpeg_and_normalizes_to_webp() -> None:
    raw = make_image("JPEG", (200, 150))
    normalized, mime, width, height = validate_and_normalize_image(
        raw,
        "image/jpeg",
        ImageLimits(max_bytes=1024 * 1024),
    )
    assert normalized
    assert mime == "image/webp"
    assert (width, height) == (200, 150)

    # Verify that the normalized bytes decode as WEBP
    with Image.open(BytesIO(normalized)) as out_img:
        assert out_img.format == "WEBP"


def test_accepts_valid_png_and_normalizes_to_webp() -> None:
    raw = make_image("PNG", (120, 80))
    normalized, mime, width, height = validate_and_normalize_image(
        raw,
        "image/png",
        ImageLimits(max_bytes=1024 * 1024),
    )
    assert normalized
    assert mime == "image/webp"
    assert (width, height) == (120, 80)


def test_accepts_valid_webp_and_reencodes() -> None:
    raw = make_image("WEBP", (150, 150))
    normalized, mime, width, height = validate_and_normalize_image(
        raw,
        "image/webp",
        ImageLimits(max_bytes=1024 * 1024),
    )
    assert normalized
    assert mime == "image/webp"
    assert (width, height) == (150, 150)


def test_rejects_empty_payload() -> None:
    with pytest.raises(InvalidImageError, match="Empty image payload"):
        validate_and_normalize_image(
            b"",
            "image/jpeg",
            ImageLimits(max_bytes=1024 * 1024),
        )


def test_rejects_oversized_payload() -> None:
    raw = make_image("JPEG")
    with pytest.raises(InvalidImageError, match="exceeds limit"):
        validate_and_normalize_image(
            raw,
            "image/jpeg",
            ImageLimits(max_bytes=len(raw) - 1),
        )


def test_rejects_unsupported_declared_mime() -> None:
    raw = make_image("JPEG")
    with pytest.raises(InvalidImageError, match="Unsupported declared MIME"):
        validate_and_normalize_image(
            raw,
            "image/svg+xml",
            ImageLimits(max_bytes=1024 * 1024),
        )


def test_rejects_corrupted_or_non_image_bytes() -> None:
    garbage = b"<svg xmlns='http://www.w3.org/2000/svg'><circle r='5'/></svg>"
    with pytest.raises(InvalidImageError, match="Corrupted or invalid image data"):
        validate_and_normalize_image(
            garbage,
            "image/jpeg",
            ImageLimits(max_bytes=1024 * 1024),
        )


def test_rejects_mime_type_mismatch() -> None:
    # Bytes are PNG, but declared as JPEG
    raw_png = make_image("PNG")
    with pytest.raises(InvalidImageError, match="MIME type mismatch"):
        validate_and_normalize_image(
            raw_png,
            "image/jpeg",
            ImageLimits(max_bytes=1024 * 1024),
        )


def test_rejects_excessive_dimensions() -> None:
    raw = make_image("JPEG", size=(5000, 100))
    with pytest.raises(InvalidImageError, match="dimensions .* exceed maximum allowed"):
        validate_and_normalize_image(
            raw,
            "image/jpeg",
            ImageLimits(max_bytes=10 * 1024 * 1024, max_width=4096, max_height=4096),
        )


def test_rejects_decompression_bomb_pixel_count() -> None:
    raw = make_image("JPEG", size=(4000, 4000))  # 16,000,000 pixels
    with pytest.raises(InvalidImageError, match="decompression bomb threshold"):
        validate_and_normalize_image(
            raw,
            "image/jpeg",
            ImageLimits(max_bytes=10 * 1024 * 1024, max_width=4096, max_height=4096, max_pixels=10_000_000),
        )
