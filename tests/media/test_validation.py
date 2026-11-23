from __future__ import annotations

import io

import pytest
from PIL import Image, ImageDraw

from fashx.media.errors import ImageValidationError
from fashx.media.validation import (
    MAX_FILE_BYTES,
    MIN_FILE_BYTES,
    detect_magic_format,
    validate_image,
)


def make_image_bytes(
    format: str = "JPEG",
    size: tuple[int, int] = (600, 600),
    color: tuple[int, int, int] = (128, 64, 32),
) -> bytes:
    img = Image.new("RGB", size, color)
    # Draw some varied content so compression doesn't collapse below 10 KB
    draw = ImageDraw.Draw(img)
    for i in range(0, size[0], 20):
        draw.line([(i, 0), (size[0] - i, size[1])], fill=(i % 255, (i * 2) % 255, (i * 3) % 255), width=2)
    buf = io.BytesIO()
    img.save(buf, format=format)
    data = buf.getvalue()
    # If smaller than 10KB, expand canvas size until >= 10KB
    if len(data) < MIN_FILE_BYTES and size[0] < 2000:
        return make_image_bytes(format, (size[0] * 2, size[1] * 2), color)
    return data


def test_detect_image_format_magic_bytes():
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 20
    assert detect_magic_format(jpeg_bytes) == "JPEG"

    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
    assert detect_magic_format(png_bytes) == "PNG"

    webp_bytes = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 20
    assert detect_magic_format(webp_bytes) == "WEBP"

    unknown_bytes = b"GIF89a" + b"\x00" * 20
    assert detect_magic_format(unknown_bytes) is None


def test_validate_valid_jpeg():
    data = make_image_bytes("JPEG", size=(500, 500))
    assert len(data) >= MIN_FILE_BYTES
    result = validate_image(data, declared_content_type="image/jpeg")

    assert result.detected_format == "JPEG"
    assert result.output_content_type == "image/webp"
    assert result.width == 500
    assert result.height == 500
    assert result.normalized_size_bytes > 0
    assert len(result.original_sha256) == 64
    assert len(result.normalized_sha256) == 64


def test_validate_valid_png():
    data = make_image_bytes("PNG", size=(400, 400))
    assert len(data) >= MIN_FILE_BYTES
    result = validate_image(data, declared_content_type="image/png")

    assert result.detected_format == "PNG"
    assert result.output_content_type == "image/webp"
    assert result.width == 400
    assert result.height == 400


def test_validate_valid_webp():
    data = make_image_bytes("WEBP", size=(600, 600))
    assert len(data) >= MIN_FILE_BYTES
    result = validate_image(data, declared_content_type="image/webp")

    assert result.detected_format == "WEBP"
    assert result.output_content_type == "image/webp"
    assert result.width == 600
    assert result.height == 600


def test_reject_unsupported_format():
    # GIF image with size >= 10KB
    img = Image.new("RGB", (400, 400), (255, 0, 0))
    draw = ImageDraw.Draw(img)
    for i in range(0, 400, 10):
        draw.line([(i, 0), (400 - i, 400)], fill=(i % 255, (i * 2) % 255, (i * 3) % 255), width=2)
    buf = io.BytesIO()
    img.save(buf, format="GIF")
    gif_data = buf.getvalue()
    assert len(gif_data) >= MIN_FILE_BYTES

    with pytest.raises(ImageValidationError) as exc_info:
        validate_image(gif_data, declared_content_type="image/gif")
    assert exc_info.value.code == "unsupported_image_format"


def test_reject_content_type_mismatch():
    # JPEG bytes declared as image/png
    data = make_image_bytes("JPEG", size=(500, 500))
    with pytest.raises(ImageValidationError) as exc_info:
        validate_image(data, declared_content_type="image/png")
    assert exc_info.value.code == "image_content_type_mismatch"


def test_reject_size_below_minimum():
    # Tiny 10x10 image under 10KB
    img = Image.new("RGB", (10, 10), (0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    tiny_data = buf.getvalue()
    assert len(tiny_data) < MIN_FILE_BYTES

    with pytest.raises(ImageValidationError) as exc_info:
        validate_image(tiny_data, declared_content_type="image/jpeg")
    assert exc_info.value.code == "image_size_below_minimum"


def test_reject_size_exceeded():
    fake_huge_data = b"\xff\xd8\xff\xe0" + b"\x00" * (MAX_FILE_BYTES + 10)
    with pytest.raises(ImageValidationError) as exc_info:
        validate_image(fake_huge_data, declared_content_type="image/jpeg")
    assert exc_info.value.code == "image_size_exceeded"


def test_reject_corrupted_image():
    # Starts with JPEG magic bytes but contains garbage
    corrupt_data = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\xff" * 15000
    with pytest.raises(ImageValidationError) as exc_info:
        validate_image(corrupt_data, declared_content_type="image/jpeg")
    assert exc_info.value.code == "image_decode_failed"


def test_reject_dimensions_exceeded():
    # Dimension > 4096 px (e.g. 4097 x 50)
    img = Image.new("RGB", (4097, 50), (255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    # Pad to ensure > 10KB
    data = buf.getvalue()
    if len(data) < MIN_FILE_BYTES:
        data = data + b"\x00" * (MIN_FILE_BYTES - len(data) + 100)

    with pytest.raises(ImageValidationError) as exc_info:
        validate_image(data, declared_content_type="image/jpeg")
    assert exc_info.value.code == "image_dimensions_exceeded"


def test_exif_metadata_stripped():
    # Create JPEG with EXIF metadata
    img = Image.new("RGB", (500, 500), (100, 150, 200))
    exif_dict = img.getexif()
    exif_dict[0x010E] = "Sensitive User Description"
    exif_dict[0x010F] = "Camera Manufacturer Brand"

    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif_dict)
    data = buf.getvalue()
    if len(data) < MIN_FILE_BYTES:
        data = make_image_bytes("JPEG", size=(600, 600))

    result = validate_image(data, declared_content_type="image/jpeg")

    # Read back normalized output WebP
    normalized_img = Image.open(io.BytesIO(result.normalized_bytes))
    norm_exif = normalized_img.getexif()
    assert 0x010E not in norm_exif
    assert 0x010F not in norm_exif
    assert len(norm_exif) == 0


def test_reject_animated_webp():
    img1 = Image.new("RGB", (200, 200), (255, 0, 0))
    img2 = Image.new("RGB", (200, 200), (0, 255, 0))
    buf = io.BytesIO()
    img1.save(buf, format="WEBP", save_all=True, append_images=[img2], duration=200, loop=0)
    data = buf.getvalue()
    if len(data) < MIN_FILE_BYTES:
        data = data + b"\x00" * (MIN_FILE_BYTES - len(data) + 100)

    with pytest.raises(ImageValidationError) as exc_info:
        validate_image(data, declared_content_type="image/webp")
    assert exc_info.value.code in ("animated_image_unsupported", "image_decode_failed")

