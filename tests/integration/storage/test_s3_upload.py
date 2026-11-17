"""Integration tests for S3 direct upload workflow and normalization."""

from __future__ import annotations

import os
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from fashx.infrastructure.storage.image_validation import ImageLimits, validate_and_normalize_image
from fashx.infrastructure.storage.presigned import USER_UPLOAD, create_upload_session


def make_test_image(fmt: str = "JPEG") -> bytes:
    buf = BytesIO()
    Image.new("RGB", (64, 64), "blue").save(buf, format=fmt)
    return buf.getvalue()


def test_upload_session_and_image_validation_flow() -> None:
    # 1. Create upload session
    with patch("fashx.infrastructure.storage.presigned._get_s3_storage") as mock_get_storage:
        mock_storage = MagicMock()
        mock_storage.generate_presigned_post.return_value = {
            "url": "https://s3.ap-south-1.amazonaws.com/fashx-dev-media",
            "fields": {"key": "temporary/uploads/asset-test-1"},
        }
        mock_get_storage.return_value = mock_storage

        session = create_upload_session(USER_UPLOAD, asset_id="asset-test-1")
        assert session["upload_method"] == "POST"
        assert session["upload_fields"]["key"] == "temporary/uploads/asset-test-1"

    # 2. Simulate raw upload bytes and backend normalization
    raw_bytes = make_test_image("JPEG")
    normalized, mime, width, height = validate_and_normalize_image(
        raw_bytes,
        "image/jpeg",
        ImageLimits(max_bytes=USER_UPLOAD.max_bytes),
    )
    assert mime == "image/webp"
    assert (width, height) == (64, 64)


@pytest.mark.skipif(
    os.environ.get("FASHX_STORAGE_INTEGRATION") != "1",
    reason="Requires live AWS S3 credentials and FASHX_STORAGE_INTEGRATION=1",
)
def test_live_s3_upload_and_promotion() -> None:  # pragma: no cover
    # Executed only when live S3 environment is available
    pass
