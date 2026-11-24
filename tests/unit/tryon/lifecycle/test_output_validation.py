"""Unit tests for provider output image validation and SSRF guards (Phase 07.4)."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from fashx.tryon.output_validation import (
    is_safe_provider_output_url,
    validate_provider_output,
)


def make_test_jpeg(size: tuple[int, int] = (512, 768), color: str = "white") -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color=color).save(buf, format="JPEG")
    return buf.getvalue()


def make_test_png(size: tuple[int, int] = (512, 768), color: str = "green") -> bytes:
    buf = io.BytesIO()
    Image.new("RGBA", size, color=color).save(buf, format="PNG")
    return buf.getvalue()


def test_valid_jpeg_output_is_normalized() -> None:
    raw = make_test_jpeg((600, 800))
    res = validate_provider_output(raw)

    assert res.content_type == "image/jpeg"
    assert res.width == 600
    assert res.height == 800
    assert len(res.sha256) == 64
    assert res.size_bytes > 0


def test_valid_png_output_is_converted_to_jpeg() -> None:
    raw = make_test_png((512, 512))
    res = validate_provider_output(raw)

    assert res.content_type == "image/jpeg"
    assert res.width == 512
    assert res.height == 512
    assert len(res.sha256) == 64


def test_corrupt_output_is_rejected() -> None:
    with pytest.raises(ValueError, match="Corrupted or invalid image data"):
        validate_provider_output(b"not-an-image-data-payload")


def test_empty_output_is_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        validate_provider_output(b"")


def test_oversized_output_is_rejected() -> None:
    # Exceeds 15 MB limit
    with pytest.raises(ValueError, match="exceeds maximum limit"):
        validate_provider_output(b"x" * (15 * 1024 * 1024 + 1))


def test_resolution_too_small_is_rejected() -> None:
    raw = make_test_jpeg((200, 200))  # Min allowed is 256x256
    with pytest.raises(ValueError, match="below minimum allowed"):
        validate_provider_output(raw)


def test_ssrf_rejects_non_https() -> None:
    assert not is_safe_provider_output_url("http://api.fashn.ai/v1/outputs/res.jpg")


def test_ssrf_rejects_localhost_and_private_ips() -> None:
    assert not is_safe_provider_output_url("https://localhost/image.jpg")
    assert not is_safe_provider_output_url("https://127.0.0.1/image.jpg")
    assert not is_safe_provider_output_url("https://169.254.169.254/latest/meta-data")
    assert not is_safe_provider_output_url("https://10.0.0.1/image.jpg")
    assert not is_safe_provider_output_url("https://192.168.1.1/image.jpg")


def test_ssrf_accepts_approved_provider_domains() -> None:
    assert is_safe_provider_output_url("https://api.fashn.ai/v1/results/abc.jpg")
    assert is_safe_provider_output_url("https://cdn.fashn.ai/outputs/123.jpg")
    assert is_safe_provider_output_url("https://fashn-outputs.s3.amazonaws.com/xyz.jpg")
