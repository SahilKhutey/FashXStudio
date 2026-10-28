"""Unit tests for byte-level image content validation and format verification."""

from io import BytesIO

import pytest
from PIL import Image

from fashx.catalog.images.validator import (
    MAX_IMAGE_BYTES,
    validate_image_bytes,
)


def make_test_image_bytes(format_name: str = "JPEG", size: tuple[int, int] = (100, 100)) -> bytes:
    buf = BytesIO()
    img = Image.new("RGB", size, color="blue")
    img.save(buf, format=format_name)
    return buf.getvalue()


def test_valid_jpeg_and_png_bytes_pass() -> None:
    jpeg_bytes = make_test_image_bytes("JPEG", (200, 300))
    validated = validate_image_bytes(jpeg_bytes)
    assert validated.image_format == "JPEG"
    assert validated.width == 200
    assert validated.height == 300
    assert len(validated.content) == len(jpeg_bytes)

    png_bytes = make_test_image_bytes("PNG", (150, 150))
    validated_png = validate_image_bytes(png_bytes)
    assert validated_png.image_format == "PNG"
    assert validated_png.width == 150
    assert validated_png.height == 150


def test_empty_image_bytes_rejected() -> None:
    with pytest.raises(ValueError, match="Image is empty"):
        validate_image_bytes(b"")


def test_oversized_byte_limit_rejected() -> None:
    # Create byte array exceeding limit
    dummy_bytes = b"0" * (MAX_IMAGE_BYTES + 10)
    with pytest.raises(ValueError, match="Image exceeds byte limit"):
        validate_image_bytes(dummy_bytes)


def test_html_and_malformed_bytes_rejected() -> None:
    html_content = b"<!DOCTYPE html><html><body><h1>Error 404</h1></body></html>"
    with pytest.raises(ValueError, match="Malformed or unrecognized"):
        validate_image_bytes(html_content)


def test_unsupported_image_format_rejected() -> None:
    # GIF format is not in ALLOWED_FORMATS (JPEG, PNG, WEBP)
    gif_buf = BytesIO()
    img = Image.new("RGB", (50, 50), color="red")
    img.save(gif_buf, format="GIF")
    with pytest.raises(ValueError, match="Unsupported image format"):
        validate_image_bytes(gif_buf.getvalue())
