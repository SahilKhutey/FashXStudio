from io import BytesIO

from PIL import Image

from api.app.tryon.domain.result_quality import validate_result_bytes


def _jpeg_bytes(width: int = 640, height: int = 800) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), (128, 128, 128)).save(buffer, format="JPEG")
    return buffer.getvalue()


def test_result_quality_accepts_valid_image() -> None:
    result = validate_result_bytes(
        _jpeg_bytes(),
        declared_content_type="image/jpeg",
        min_width=512,
        min_height=512,
        max_bytes=2_000_000,
    )
    assert result.accepted is True
    assert result.width == 640
    assert result.height == 800
    assert result.sha256
    assert result.content_type == "image/jpeg"


def test_result_quality_rejects_too_small_image() -> None:
    result = validate_result_bytes(
        _jpeg_bytes(256, 256),
        declared_content_type="image/jpeg",
        min_width=512,
        min_height=512,
        max_bytes=2_000_000,
    )
    assert result.accepted is False
    assert "result_resolution_too_low" in result.reasons


def test_result_quality_rejects_non_image_payload() -> None:
    result = validate_result_bytes(
        b"not-an-image",
        declared_content_type="text/plain",
        min_width=512,
        min_height=512,
        max_bytes=2_000_000,
    )
    assert result.accepted is False
    assert "invalid_image" in result.reasons
