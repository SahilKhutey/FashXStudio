import io

import pytest
from PIL import Image

from fashx.core.errors import ValidationError
from fashx.security.uploads import sanitize_photo


def create_test_image(format="JPEG", size=(200, 200), exif_dict=None) -> bytes:
    img = Image.new("RGB", size, color="blue")
    buf = io.BytesIO()
    if exif_dict:
        exif = img.getexif()
        for k, v in exif_dict.items():
            exif[k] = v
        img.save(buf, format=format, exif=exif)
    else:
        img.save(buf, format=format)
    return buf.getvalue()


def test_sanitize_valid_jpeg():
    raw = create_test_image("JPEG", (300, 300))
    cleaned = sanitize_photo(raw)
    assert len(cleaned) > 0

    with Image.open(io.BytesIO(cleaned)) as img:
        assert img.format == "JPEG"
        assert img.size == (300, 300)


def test_sanitize_valid_png():
    raw = create_test_image("PNG", (250, 250))
    cleaned = sanitize_photo(raw)
    with Image.open(io.BytesIO(cleaned)) as img:
        assert img.format == "PNG"
        assert img.size == (250, 250)


def test_sanitize_valid_webp():
    raw = create_test_image("WEBP", (200, 200))
    cleaned = sanitize_photo(raw)
    with Image.open(io.BytesIO(cleaned)) as img:
        assert img.format == "WEBP"
        assert img.size == (200, 200)


def test_reject_corrupt_payload():
    with pytest.raises(ValidationError) as exc:
        sanitize_photo(b"<script>alert('xss')</script>")
    assert "Corrupted or invalid" in str(exc.value)


def test_reject_unsupported_format():
    # GIF is not in allowed formats
    img = Image.new("RGB", (200, 200))
    buf = io.BytesIO()
    img.save(buf, format="GIF")
    with pytest.raises(ValidationError) as exc:
        sanitize_photo(buf.getvalue())
    assert "Unsupported image format" in str(exc.value)


def test_reject_dimensions_too_small():
    raw = create_test_image("JPEG", (50, 50))
    with pytest.raises(ValidationError) as exc:
        sanitize_photo(raw, min_dimension=100)
    assert "below minimum required" in str(exc.value)


def test_reject_dimensions_too_large():
    raw = create_test_image("JPEG", (5000, 200))
    with pytest.raises(ValidationError) as exc:
        sanitize_photo(raw, max_dimension=4096)
    assert "exceed maximum allowed" in str(exc.value)


def test_reject_bytes_too_large():
    raw = create_test_image("JPEG", (200, 200))
    with pytest.raises(ValidationError) as exc:
        sanitize_photo(raw, max_bytes=10)
    assert "exceeds maximum permitted size" in str(exc.value)


def test_strips_exif_metadata():
    # EXIF tag 0x010E is ImageDescription
    raw_with_exif = create_test_image("JPEG", (200, 200), exif_dict={0x010E: "Secret Location GPS"})
    with Image.open(io.BytesIO(raw_with_exif)) as img:
        assert 0x010E in img.getexif()

    cleaned = sanitize_photo(raw_with_exif)
    with Image.open(io.BytesIO(cleaned)) as img:
        # Exif tag should be stripped
        assert 0x010E not in img.getexif()
