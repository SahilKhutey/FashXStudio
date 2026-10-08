import io

from api.app.tryon.quality_validator import PostInferenceQualityValidator
from PIL import Image


def _generate_png(size: tuple[int, int], color: tuple[int, int, int]) -> bytes:
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _generate_textured_png(size: tuple[int, int]) -> bytes:
    # Generates a gradient pattern with healthy luminance variance
    img = Image.new("RGB", size)
    pixels = img.load()
    w, h = size
    for y in range(h):
        for x in range(w):
            pixels[x, y] = (int((x / w) * 200) + 20, int((y / h) * 180) + 30, 100)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_post_inference_quality_accepts_healthy_render() -> None:
    textured = _generate_textured_png((512, 512))
    res = PostInferenceQualityValidator.validate(textured)

    assert res.is_acceptable is True
    assert res.failure_reason is None
    assert res.structural_score > 0.5
    assert res.contrast_score > 12.0


def test_post_inference_quality_rejects_black_frame() -> None:
    black = _generate_png((512, 512), (5, 5, 5))
    res = PostInferenceQualityValidator.validate(black)

    assert res.is_acceptable is False
    assert "underexposed / black frame" in res.failure_reason


def test_post_inference_quality_rejects_white_blown_out_frame() -> None:
    white = _generate_png((512, 512), (250, 250, 250))
    res = PostInferenceQualityValidator.validate(white)

    assert res.is_acceptable is False
    assert "blown out / overexposed" in res.failure_reason


def test_post_inference_quality_rejects_flat_degenerate_frame() -> None:
    # Flat grey frame has 0 contrast std
    flat = _generate_png((512, 512), (128, 128, 128))
    res = PostInferenceQualityValidator.validate(flat)

    assert res.is_acceptable is False
    assert "lacks contrast" in res.failure_reason


def test_post_inference_quality_rejects_tiny_resolution() -> None:
    tiny = _generate_textured_png((128, 128))
    res = PostInferenceQualityValidator.validate(tiny)

    assert res.is_acceptable is False
    assert "resolution below minimum threshold" in res.failure_reason
