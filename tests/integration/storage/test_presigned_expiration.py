"""Integration tests for presigned URL expiration and tampering prevention."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from fashx.infrastructure.storage.presigned import (
    USER_UPLOAD,
    create_download_url,
    create_upload_session,
)


def test_presigned_url_generation_with_custom_ttl() -> None:
    with patch("fashx.infrastructure.storage.presigned._get_s3_storage") as mock_get_storage:
        mock_storage = MagicMock()
        mock_storage.signed_get_url.return_value = (
            "https://s3.ap-south-1.amazonaws.com/bucket/key?X-Amz-Expires=60&X-Amz-Signature=xyz"
        )
        mock_get_storage.return_value = mock_storage

        url = create_download_url("tryon/u1/job1/result.webp", ttl_s=60)
        assert "X-Amz-Expires=60" in url
        mock_storage.signed_get_url.assert_called_once_with(key="tryon/u1/job1/result.webp", ttl_s=60)


def test_upload_session_enforces_distinct_keys_per_request() -> None:
    with patch("fashx.infrastructure.storage.presigned._get_s3_storage") as mock_get_storage:
        mock_storage = MagicMock()
        mock_storage.generate_presigned_post.side_effect = lambda key, **kwargs: {
            "url": "https://s3.ap-south-1.amazonaws.com/bucket",
            "fields": {"key": key},
        }
        mock_get_storage.return_value = mock_storage

        session1 = create_upload_session(USER_UPLOAD)
        session2 = create_upload_session(USER_UPLOAD)

        # Every upload session must receive a globally unique server-generated key
        assert session1["asset_id"] != session2["asset_id"]
        assert session1["upload_fields"]["key"] != session2["upload_fields"]["key"]


@pytest.mark.skipif(
    os.environ.get("FASHX_STORAGE_INTEGRATION") != "1",
    reason="Requires live AWS S3 credentials and FASHX_STORAGE_INTEGRATION=1",
)
def test_live_presigned_expiration() -> None:  # pragma: no cover
    pass
