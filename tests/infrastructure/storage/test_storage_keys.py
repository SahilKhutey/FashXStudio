"""Unit tests for S3 storage key validation and traversal prevention."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from fashx.infrastructure.storage.deletion import delete_object, object_exists
from fashx.infrastructure.storage.presigned import (
    PRODUCT_IMAGE_UPLOAD,
    USER_UPLOAD,
    create_download_url,
    create_upload_session,
    validate_key,
)


@pytest.mark.parametrize(
    "invalid_key",
    [
        "",
        "/",
        "/users/a/file.webp",
        "../users/a/file.webp",
        "users/../other/file.webp",
        "tryon/../../etc/passwd",
    ],
)
def test_validate_key_rejects_invalid_and_traversal_paths(invalid_key: str) -> None:
    with pytest.raises(ValueError, match="Invalid object key"):
        validate_key(invalid_key)


def test_create_download_url_rejects_invalid_key() -> None:
    with pytest.raises(ValueError, match="Invalid object key"):
        create_download_url(key="/malicious/path.webp")


def test_delete_object_rejects_invalid_key() -> None:
    with pytest.raises(ValueError, match="Invalid object key"):
        delete_object(key="../secret")


def test_object_exists_rejects_invalid_key() -> None:
    with pytest.raises(ValueError, match="Invalid object key"):
        object_exists(key="")


def test_create_upload_session_generates_safe_opaque_key() -> None:
    with patch("fashx.infrastructure.storage.presigned._get_s3_storage") as mock_get_storage:
        mock_storage = MagicMock()
        mock_storage.generate_presigned_post.return_value = {
            "url": "https://s3.ap-south-1.amazonaws.com/fashx-dev-media",
            "fields": {"key": "temporary/uploads/test-uuid-123"},
        }
        mock_get_storage.return_value = mock_storage

        session = create_upload_session(USER_UPLOAD, asset_id="test-uuid-123")

        assert session["asset_id"] == "test-uuid-123"
        assert session["upload_method"] == "POST"
        assert session["upload_url"] == "https://s3.ap-south-1.amazonaws.com/fashx-dev-media"
        assert session["upload_fields"]["key"] == "temporary/uploads/test-uuid-123"
        assert session["expires_in"] == 300


def test_create_upload_session_product_image_policy() -> None:
    with patch("fashx.infrastructure.storage.presigned._get_s3_storage") as mock_get_storage:
        mock_storage = MagicMock()
        mock_storage.generate_presigned_post.return_value = {
            "url": "https://s3.ap-south-1.amazonaws.com/fashx-dev-media",
            "fields": {"key": "temporary/ingest/feed-asset-456"},
        }
        mock_get_storage.return_value = mock_storage

        session = create_upload_session(PRODUCT_IMAGE_UPLOAD, asset_id="feed-asset-456")

        assert session["asset_id"] == "feed-asset-456"
        assert "temporary/ingest/" in session["upload_fields"]["key"]
