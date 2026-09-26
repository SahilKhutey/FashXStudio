import io

from PIL import Image

from api.app.profile.capture.validator import PhotoQualityValidator
from schemas.common.enums import PhotoStatus


def make_photo(
    width: int, height: int, color: tuple[int, int, int], add_contrast: bool = True
) -> bytes:
    img = Image.new("RGB", (width, height), color)
    if add_contrast:
        # Add contrast gradient so stddev is above threshold
        for x in range(width // 2):
            for y in range(height):
                img.putpixel(
                    (x, y), (max(0, color[0] - 40), max(0, color[1] - 40), max(0, color[2] - 40))
                )
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_photo_quality_validator_passes_valid_portrait() -> None:
    # 600x800 portrait, balanced lighting (130, 110, 95)
    data = make_photo(600, 800, (140, 120, 105), add_contrast=True)
    res = PhotoQualityValidator.validate_photo_bytes(data)
    assert res.passed is True
    assert res.status == PhotoStatus.ACCEPTED
    assert res.reject_reason is None
    assert res.metrics["width"] == 600.0
    assert res.metrics["height"] == 800.0


def test_photo_quality_validator_rejects_low_resolution() -> None:
    # 300x400 (under 512x512)
    data = make_photo(300, 400, (130, 110, 95))
    res = PhotoQualityValidator.validate_photo_bytes(data)
    assert res.passed is False
    assert res.status == PhotoStatus.REJECTED
    assert "resolution" in res.reject_reason.lower()


def test_photo_quality_validator_rejects_landscape_orientation() -> None:
    # 900x600 (aspect ratio 1.5 > 1.25)
    data = make_photo(900, 600, (130, 110, 95))
    res = PhotoQualityValidator.validate_photo_bytes(data)
    assert res.passed is False
    assert res.status == PhotoStatus.REJECTED
    assert "landscape" in res.reject_reason.lower()


def test_photo_quality_validator_rejects_underexposed() -> None:
    # Very dark image (mean luminance < 40)
    data = make_photo(600, 800, (25, 25, 25))
    res = PhotoQualityValidator.validate_photo_bytes(data)
    assert res.passed is False
    assert res.status == PhotoStatus.REJECTED
    assert "too dark" in res.reject_reason.lower()


def test_photo_quality_validator_rejects_overexposed() -> None:
    # Extremely bright washed out image (mean luminance > 220)
    data = make_photo(600, 800, (245, 245, 245))
    res = PhotoQualityValidator.validate_photo_bytes(data)
    assert res.passed is False
    assert res.status == PhotoStatus.REJECTED
    assert "overexposed" in res.reject_reason.lower()
