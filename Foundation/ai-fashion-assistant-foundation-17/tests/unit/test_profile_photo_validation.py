from io import BytesIO

from PIL import Image

from workers.profile_photo.domain.validation import BasicPhotoValidator


def make_image(width: int = 640, height: int = 960, color: tuple[int, int, int] = (220, 220, 220)) -> bytes:
    image = Image.new("RGB", (width, height), color)
    buf = BytesIO()
    image.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def test_invalid_binary_is_rejected() -> None:
    result = BasicPhotoValidator().validate(b"not-an-image", photo_type="tryon_reference")
    assert result.accepted is False
    assert result.reason == "invalid_image"
    assert len(result.content_sha256) == 64


def test_low_resolution_is_rejected() -> None:
    result = BasicPhotoValidator().validate(make_image(200, 300), photo_type="tryon_reference")
    assert result.accepted is False
    assert result.reason == "insufficient_resolution"


def test_extreme_aspect_ratio_is_rejected() -> None:
    result = BasicPhotoValidator().validate(make_image(3000, 700), photo_type="tryon_reference")
    assert result.accepted is False
    assert result.reason == "unsupported_aspect_ratio"


def test_valid_image_reaches_presence_gate() -> None:
    result = BasicPhotoValidator().validate(make_image(), photo_type="tryon_reference")
    assert result.reason in {None, "person_not_detected"}
    assert result.width == 640
    assert result.height == 960
    assert result.image_format in {"jpeg", "jpg"}
