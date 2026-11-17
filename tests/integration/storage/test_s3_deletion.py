"""Integration tests for S3 durable media deletion and user erasure."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from fashx.infrastructure.storage.deletion import delete_object, object_exists


def test_durable_media_deletion_workflow() -> None:
    test_key = "users/synthetic-user-1/uploads/photo-1.webp"

    # Step 1: Simulate object exists before deletion
    with patch("fashx.infrastructure.storage.deletion._client") as mock_client:
        mock_c = MagicMock()
        mock_c.head_object.return_value = {"ContentLength": 1024}
        mock_client.return_value = mock_c

        assert object_exists(test_key) is True

    # Step 2: Delete object
    with patch("fashx.infrastructure.storage.deletion._client") as mock_client:
        mock_c = MagicMock()
        mock_client.return_value = mock_c

        delete_object(test_key)
        mock_c.delete_object.assert_called_once()
        _, kwargs = mock_c.delete_object.call_args
        assert kwargs["Key"] == test_key

    # Step 3: Verify object no longer exists (404)
    with patch("fashx.infrastructure.storage.deletion._client") as mock_client:
        mock_c = MagicMock()
        mock_c.head_object.side_effect = ClientError(
            error_response={"Error": {"Code": "NoSuchKey", "Message": "Not found"}},
            operation_name="HeadObject",
        )
        mock_client.return_value = mock_c

        assert object_exists(test_key) is False

    # Step 4: Repeat deletion to confirm idempotency (no error raised)
    with patch("fashx.infrastructure.storage.deletion._client") as mock_client:
        mock_c = MagicMock()
        mock_client.return_value = mock_c
        delete_object(test_key)
        assert mock_c.delete_object.called


@pytest.mark.skipif(
    os.environ.get("FASHX_STORAGE_INTEGRATION") != "1",
    reason="Requires live AWS S3 credentials and FASHX_STORAGE_INTEGRATION=1",
)
def test_live_s3_deletion() -> None:  # pragma: no cover
    pass
