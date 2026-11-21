from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from fashx.catalog.embeddings.preprocessing import (
    PreprocessingConfig,
    PreprocessingError,
    preprocess_image,
)


def test_emb_008_bounds_validation() -> None:
    """Verify EMB-008: Preprocessing rejects images below 100x100 or exceeding max bounds."""
    cfg = PreprocessingConfig(min_dimension=100, max_dimension=4096, max_aspect_ratio=4.0)

    # 1. Below minimum (50x50)
    small_img = Image.new("RGB", (50, 50), color=(10, 10, 10))
    buf_small = BytesIO()
    small_img.save(buf_small, format="JPEG")
    with pytest.raises(PreprocessingError, match="below minimum allowed"):
        preprocess_image(buf_small.getvalue(), config=cfg)

    # 2. Extreme aspect ratio (500x50 = 10:1)
    pano_img = Image.new("RGB", (500, 50), color=(10, 10, 10))
    # width is 500 but height is 50, below min_dimension
    # Let's test 1000x200 (aspect ratio 5:1, both >= 100)
    pano_img2 = Image.new("RGB", (1000, 200), color=(10, 10, 10))
    buf_pano = BytesIO()
    pano_img2.save(buf_pano, format="JPEG")
    with pytest.raises(PreprocessingError, match="aspect ratio.*exceeds maximum"):
        preprocess_image(buf_pano.getvalue(), config=cfg)


def test_emb_009_exif_normalization() -> None:
    """Verify EMB-009: Preprocessing normalizes EXIF orientation correctly."""
    # Create image with EXIF orientation tag 6 (90 deg CW rotation)
    img = Image.new("RGB", (200, 150), color=(50, 100, 150))
    exif = img.getexif()
    exif[0x0112] = 6  # Orientation: Rotate 90 CW
    buf = BytesIO()
    img.save(buf, format="JPEG", exif=exif)

    out = preprocess_image(buf.getvalue())
    assert out.size == (224, 224)
    assert out.mode == "RGB"


def test_emb_010_aspect_preservation_and_padding() -> None:
    """Verify EMB-010: Aspect ratio preserved with uniform neutral padding on square canvas."""
    # Create a tall 200x400 image (1:2 aspect ratio)
    img = Image.new("RGB", (200, 400), color=(255, 0, 0))
    buf = BytesIO()
    img.save(buf, format="JPEG")

    out = preprocess_image(buf.getvalue(), PreprocessingConfig(target_size=(224, 224)))
    assert out.size == (224, 224)
    # Target height 224, scale = 224 / 400 = 0.56, scaled width = 112
    # Offset x should be around (224 - 112) / 2 = 56
    # Pixels at edge (0, 0) must be neutral background (255, 255, 255)
    corner_pixel = out.getpixel((0, 0))
    assert corner_pixel == (255, 255, 255)

    # Pixel in center (112, 112) should contain the garment color (approx red)
    center_pixel = out.getpixel((112, 112))
    assert center_pixel[0] > 200  # High red component


def test_emb_011_color_space_conversion(sample_png_rgba_bytes: bytes) -> None:
    """Verify EMB-011: Converts transparent RGBA or Grayscale images to 3-channel RGB."""
    # 1. RGBA with alpha channel
    out_rgba = preprocess_image(sample_png_rgba_bytes)
    assert out_rgba.mode == "RGB"
    assert out_rgba.size == (224, 224)

    # 2. Grayscale (L mode)
    gray_img = Image.new("L", (200, 200), color=128)
    buf_gray = BytesIO()
    gray_img.save(buf_gray, format="JPEG")
    out_gray = preprocess_image(buf_gray.getvalue())
    assert out_gray.mode == "RGB"
    assert out_gray.size == (224, 224)


def test_emb_012_corrupt_file_handling() -> None:
    """Verify EMB-012: Preprocessing safely rejects corrupt or truncated image bytes."""
    # 1. Empty bytes
    with pytest.raises(PreprocessingError, match="empty"):
        preprocess_image(b"")

    # 2. Random garbage bytes
    with pytest.raises(PreprocessingError, match="Failed to decode"):
        preprocess_image(b"NOT_AN_IMAGE_RANDOM_GARBAGE_PAYLOAD_1234567890")

    # 3. Truncated JPEG header
    with pytest.raises(PreprocessingError, match="Failed to decode"):
        preprocess_image(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01")
