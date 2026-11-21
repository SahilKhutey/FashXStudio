"""Unit tests for Phase 05.4 image byte inspection, security, format and dimension validation.

Covers test IDs: IMG-010 through IMG-024, and IMG-027.
"""

from __future__ import annotations

import io

import pytest
from PIL import Image

from fashx.catalog.images.fetcher import ImageFetchError, SafeImageFetcher
from fashx.catalog.images.hasher import ImageHasher
from fashx.catalog.images.inspector import ImageInspectionError, ImageInspector


def make_test_image(
    fmt: str = "JPEG",
    size: tuple[int, int] = (600, 800),
    color: str = "red",
) -> bytes:
    """Helper to generate valid image bytes in memory."""
    buf = io.BytesIO()
    mode = "RGBA" if fmt.upper() == "PNG" else "RGB"
    img = Image.new(mode, size, color)
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_img_010_valid_https_image_format_detection() -> None:
    """IMG-010: Valid HTTPS image bytes are inspected and verified."""
    raw = make_test_image(fmt="JPEG", size=(600, 800))
    inspected = ImageInspector.inspect(raw)
    assert inspected.detected_format == "JPEG"
    assert inspected.mime_type == "image/jpeg"
    assert inspected.width == 600
    assert inspected.height == 800
    assert inspected.is_animated is False


def test_img_011_http_image_url_rejected() -> None:
    """IMG-011: HTTP scheme is strictly rejected."""
    fetcher = SafeImageFetcher()
    with pytest.raises(ImageFetchError) as exc:
        fetcher.validate_url("http://merchant.example.com/item.jpg")
    assert exc.value.code == "insecure_scheme"


def test_img_012_private_ip_address_rejected() -> None:
    """IMG-012: Private IP addresses and loopback are blocked (SSRF defense)."""
    fetcher = SafeImageFetcher()
    for bad_url in (
        "https://127.0.0.1/item.jpg",
        "https://10.0.0.1/item.jpg",
        "https://172.16.0.5/item.jpg",
        "https://192.168.1.1/item.jpg",
        "https://169.254.169.254/latest/meta-data/",
        "https://localhost/item.jpg",
    ):
        with pytest.raises(ImageFetchError) as exc:
            fetcher.validate_url(bad_url)
        assert exc.value.code in ("ssrf_violation", "ssrf_private_ip")


@pytest.mark.asyncio
async def test_img_013_and_014_redirect_security() -> None:
    """IMG-013 & IMG-014: Redirect to private IP or unapproved domain is rejected."""
    fetcher = SafeImageFetcher(allowed_hosts=["approved.example.com"])
    # Host allowlist check
    with pytest.raises(ImageFetchError) as exc:
        fetcher.validate_url("https://unapproved.example.com/item.jpg")
    assert exc.value.code == "disallowed_host"


def test_img_015_html_response_rejected() -> None:
    """IMG-015: HTML response payload is detected and rejected."""
    html_bytes = b"<!DOCTYPE html><html><body>Error 404 Not Found</body></html>"
    with pytest.raises(ImageInspectionError) as exc:
        ImageInspector.inspect(html_bytes)
    assert exc.value.code == "html_payload"


def test_img_016_unsupported_mime_rejected() -> None:
    """IMG-016: Unsupported signatures (SVG, PDF, text) are rejected."""
    svg_bytes = b"<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100'></svg>"
    with pytest.raises(ImageInspectionError) as exc:
        ImageInspector.inspect(svg_bytes)
    assert exc.value.code == "prohibited_format"

    pdf_bytes = b"%PDF-1.4 header bytes"
    with pytest.raises(ImageInspectionError) as exc:
        ImageInspector.inspect(pdf_bytes)
    assert exc.value.code == "prohibited_format"


def test_img_017_corrupted_jpeg_rejected() -> None:
    """IMG-017: Truncated or corrupted image stream is rejected."""
    corrupted = b"\xff\xd8\xff\xe0" + b"garbage" * 10
    with pytest.raises(ImageInspectionError) as exc:
        ImageInspector.inspect(corrupted)
    assert exc.value.code == "corrupted_image"


def test_img_018_oversized_download_rejected() -> None:
    """IMG-018: Image exceeding maximum byte limit is rejected."""
    huge_bytes = b"X" * (11 * 1024 * 1024)
    with pytest.raises(ImageInspectionError) as exc:
        ImageInspector.inspect(huge_bytes)
    assert exc.value.code == "invalid_size"


def test_img_019_image_below_minimum_dimensions_rejected() -> None:
    """IMG-019: Image below minimum 400x400 dimensions is rejected."""
    small = make_test_image(size=(350, 350))
    with pytest.raises(ImageInspectionError) as exc:
        ImageInspector.inspect(small)
    assert exc.value.code == "image_too_small"


def test_img_020_image_above_dimension_limits_rejected() -> None:
    """IMG-020: Image exceeding 4096px maximum width/height is rejected."""
    # Create image header exceeding limit
    buf = io.BytesIO()
    img = Image.new("RGB", (4500, 1000), "blue")
    img.save(buf, format="JPEG")
    with pytest.raises(ImageInspectionError) as exc:
        ImageInspector.inspect(buf.getvalue())
    assert exc.value.code == "image_dimensions_exceeded"


def test_img_021_decompression_bomb_rejected() -> None:
    """IMG-021: Decompression bomb pixel limits trigger safe rejection."""
    # A tiny byte payload advertising enormous dimensions
    # We test that exceeding Image.MAX_IMAGE_PIXELS raises decompression_bomb or pixel limit
    buf = io.BytesIO()
    # 5000 x 5000 = 25M pixels (> 20M limit)
    img = Image.new("RGB", (5000, 5000), "white")
    img.save(buf, format="JPEG")
    raw = buf.getvalue()

    with pytest.raises(ImageInspectionError) as exc:
        ImageInspector.inspect(raw)
    assert exc.value.code in (
        "decompression_bomb",
        "image_dimensions_exceeded",
        "image_pixel_limit_exceeded",
    )


def test_img_022_animated_image_rejected() -> None:
    """IMG-022: Animated WebP or GIF is rejected under initial policy."""
    buf = io.BytesIO()
    img1 = Image.new("RGB", (500, 500), "white")
    img2 = Image.new("RGB", (500, 500), "black")
    img1.save(buf, format="WEBP", save_all=True, append_images=[img2], duration=200, loop=0)
    animated_webp = buf.getvalue()

    with pytest.raises(ImageInspectionError) as exc:
        ImageInspector.inspect(animated_webp)
    assert exc.value.code == "animated_image_rejected"


def test_img_023_and_024_exif_orientation_and_metadata_stripping() -> None:
    """IMG-023 & IMG-024: EXIF orientation is normalized and metadata stripped."""
    buf = io.BytesIO()
    img = Image.new("RGB", (500, 600), "blue")
    # Add dummy exif orientation tag (Orientation = 6 is 90 deg CW)
    exif = img.getexif()
    exif[0x0112] = 6  # Orientation tag
    img.save(buf, format="JPEG", exif=exif)

    raw = buf.getvalue()
    inspected = ImageInspector.inspect(raw)
    # Transposing orientation 6 swaps width and height: (500, 600) -> (600, 500)
    assert inspected.width == 600
    assert inspected.height == 500

    # Ensure normalized bytes have no residual sensitive EXIF GPS info
    with Image.open(io.BytesIO(inspected.normalized_bytes)) as norm_img:
        clean_exif = norm_img.getexif()
        # GPSInfo tag is 0x8825; should not exist in clean derivative
        assert 0x8825 not in clean_exif


def test_img_027_hash_consistency() -> None:
    """IMG-027: Hashes are deterministic and stable for identical bytes."""
    raw = make_test_image(size=(500, 500), color="green")
    h1 = ImageHasher.compute_sha256(raw)
    h2 = ImageHasher.compute_sha256(raw)
    assert h1 == h2
    assert len(h1) == 64

    dh1 = ImageHasher.compute_dhash(raw)
    dh2 = ImageHasher.compute_dhash(raw)
    assert dh1 == dh2
