from __future__ import annotations

import io

import pytest
from PIL import Image

from fashx.catalog.images.preparation import SafeImageValidator
from fashx.catalog.images.validator import (
    ValidatedImage,
    validate_image_bytes,
)


def make_test_image(width: int, height: int, fmt: str = "JPEG") -> bytes:
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_validate_image_empty_bytes() -> None:
    with pytest.raises(ValueError, match="Image is empty"):
        validate_image_bytes(b"")


def test_validate_image_corrupt_bytes() -> None:
    with pytest.raises(ValueError, match="Malformed or unrecognized"):
        validate_image_bytes(b"not_an_image_random_noise_1234567890")


def test_validate_image_too_small() -> None:
    small_img = make_test_image(64, 64)
    with pytest.raises(ValueError, match="below minimum required"):
        validate_image_bytes(small_img)


def test_validate_image_valid_formats() -> None:
    for fmt in ("JPEG", "PNG", "WEBP"):
        img_bytes = make_test_image(256, 256, fmt=fmt)
        res = validate_image_bytes(img_bytes)
        assert isinstance(res, ValidatedImage)
        assert res.image_format == fmt
        assert res.width == 256
        assert res.height == 256


def test_source_permission_evaluation() -> None:
    # Cleared source with rights
    res_cleared = SafeImageValidator.evaluate_permissions(
        image_url="https://images.example.com/item1.jpg",
        source_status="cleared",
        source_rights_display=True,
        source_rights_tryon=True,
        source_image_policy="mirror",
        item_image_rights="licensed",
        item_tryon_rights=True,
    )
    assert res_cleared.display_eligible is True
    assert res_cleared.tryon_eligible is True

    # Blocked/uncleared source
    res_blocked = SafeImageValidator.evaluate_permissions(
        image_url="https://images.example.com/item1.jpg",
        source_status="pending_review",
        source_rights_display=False,
        source_rights_tryon=False,
        source_image_policy="cache_and_serve",
        item_image_rights="restricted",
        item_tryon_rights=False,
    )
    assert res_blocked.display_eligible is False
    assert res_blocked.tryon_eligible is False
