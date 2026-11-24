"""Unit tests for ImageInspector technical validation (Phase 07.3)."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from fashx.tryon.validation.config import ImageValidationConfig
from fashx.tryon.validation.error_codes import (
    FORMAT_UNSUPPORTED,
    IMAGE_CORRUPTED,
    IMAGE_TOO_LARGE,
    IMAGE_TOO_SMALL,
)
from fashx.tryon.validation.image_inspector import (
    ImageInspectionError,
    ImageInspector,
)


def make_test_image(
    fmt: str = "JPEG",
    size: tuple[int, int] = (1024, 1024),
    color: str = "blue",
) -> bytes:
    buf = io.BytesIO()
    mode = "RGBA" if fmt == "PNG" else "RGB"
    Image.new(mode, size, color=color).save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture
def inspector() -> ImageInspector:
    return ImageInspector(ImageValidationConfig())


def test_valid_jpeg(inspector: ImageInspector) -> None:
    raw = make_test_image("JPEG", (1024, 1024))
    res = inspector.inspect(raw)
    assert res.detected_format == "JPEG"
    assert res.width == 1024
    assert res.height == 1024
    assert len(res.original_sha256) == 64
    assert len(res.normalized_sha256) == 64


def test_valid_png_converts_to_rgb(inspector: ImageInspector) -> None:
    raw = make_test_image("PNG", (800, 1200))
    res = inspector.inspect(raw)
    assert res.detected_format == "PNG"
    assert res.width == 800
    assert res.height == 1200
    # Normalized bytes must be valid JPEG
    with Image.open(io.BytesIO(res.normalized_bytes)) as norm:
        assert norm.format == "JPEG"
        assert norm.mode == "RGB"


def test_valid_webp(inspector: ImageInspector) -> None:
    raw = make_test_image("WEBP", (600, 900))
    res = inspector.inspect(raw)
    assert res.detected_format == "WEBP"
    assert res.width == 600
    assert res.height == 900


def test_empty_or_too_small_bytes_rejected(inspector: ImageInspector) -> None:
    with pytest.raises(ImageInspectionError) as exc:
        inspector.inspect(b"")
    assert exc.value.code == IMAGE_CORRUPTED

    with pytest.raises(ImageInspectionError) as exc_small:
        inspector.inspect(b"too_short")
    assert exc_small.value.code == IMAGE_CORRUPTED


def test_unsupported_formats_rejected(inspector: ImageInspector) -> None:
    # GIF format
    gif_raw = make_test_image("GIF", (600, 600))
    with pytest.raises(ImageInspectionError) as exc_gif:
        inspector.inspect(gif_raw)
    assert exc_gif.value.code == FORMAT_UNSUPPORTED

    # Plain text masquerading as image
    with pytest.raises(ImageInspectionError) as exc_text:
        inspector.inspect(b"<html>not an image raster data at all</html>")
    assert exc_text.value.code == IMAGE_CORRUPTED


def test_image_dimensions_below_minimum_rejected(inspector: ImageInspector) -> None:
    # 300x300 is below 512x512
    tiny = make_test_image("JPEG", (300, 300))
    with pytest.raises(ImageInspectionError) as exc:
        inspector.inspect(tiny)
    assert exc.value.code == IMAGE_TOO_SMALL


def test_image_dimensions_above_maximum_rejected(inspector: ImageInspector) -> None:
    # 5000x2000 has width > 4096
    huge = make_test_image("JPEG", (5000, 2000))
    with pytest.raises(ImageInspectionError) as exc:
        inspector.inspect(huge)
    assert exc.value.code == IMAGE_TOO_LARGE


def test_file_size_exceeded_rejected() -> None:
    # Config with 1 KB maximum
    strict_inspector = ImageInspector(ImageValidationConfig(max_file_size_bytes=1024))
    raw = make_test_image("JPEG", (1024, 1024))
    with pytest.raises(ImageInspectionError) as exc:
        strict_inspector.inspect(raw)
    assert exc.value.code == IMAGE_TOO_LARGE
