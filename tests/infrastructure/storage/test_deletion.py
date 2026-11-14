"""Unit tests for S3 deletion service and existence check classification."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from fashx.infrastructure.storage.deletion import delete_object, delete_prefix, object_exists


def make_client_error(code: str, http_status: int) -> ClientError:
    return ClientError(
        error_response={"Error": {"Code": code, "Message": "Test Error"}},
        operation_name="HeadObject",
    )


def test_delete_object_invokes_s3_client_correctly() -> None:
    with patch("fashx.infrastructure.storage.deletion._client") as mock_get_client:
        mock_c = MagicMock()
        mock_get_client.return_value = mock_c

        delete_object("users/u123/uploads/photo.jpg")

        mock_c.delete_object.assert_called_once()
        _, kwargs = mock_c.delete_object.call_args
        assert kwargs["Key"] == "users/u123/uploads/photo.jpg"


def test_object_exists_returns_true_on_success() -> None:
    with patch("fashx.infrastructure.storage.deletion._client") as mock_get_client:
        mock_c = MagicMock()
        mock_c.head_object.return_value = {"ContentLength": 1024}
        mock_get_client.return_value = mock_c

        assert object_exists("tryon/job-1/result.webp") is True
        mock_c.head_object.assert_called_once()


def test_object_exists_returns_false_on_404_or_nosuchkey() -> None:
    with patch("fashx.infrastructure.storage.deletion._client") as mock_get_client:
        mock_c = MagicMock()
        mock_c.head_object.side_effect = ClientError(
            error_response={"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
            operation_name="HeadObject",
        )
        mock_get_client.return_value = mock_c

        assert object_exists("users/u123/nonexistent.jpg") is False


def test_object_exists_reraises_on_permission_or_server_error() -> None:
    with patch("fashx.infrastructure.storage.deletion._client") as mock_get_client:
        mock_c = MagicMock()
        mock_c.head_object.side_effect = ClientError(
            error_response={"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
            operation_name="HeadObject",
        )
        mock_get_client.return_value = mock_c

        with pytest.raises(ClientError):
            object_exists("users/u123/protected.jpg")


def test_delete_prefix_paginates_and_deletes_batches() -> None:
    with patch("fashx.infrastructure.storage.deletion._client") as mock_get_client:
        mock_c = MagicMock()
        # Simulate 2 pages of results
        mock_c.list_objects_v2.side_effect = [
            {
                "Contents": [{"Key": f"temporary/test/file_{i}.txt"} for i in range(2)],
                "IsTruncated": True,
                "NextContinuationToken": "token-1",
            },
            {
                "Contents": [{"Key": "temporary/test/file_2.txt"}],
                "IsTruncated": False,
            },
        ]
        mock_get_client.return_value = mock_c

        count = delete_prefix("temporary/test/")

        assert count == 3
        assert mock_c.delete_objects.call_count == 2
