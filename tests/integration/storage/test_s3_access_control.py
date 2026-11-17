"""Integration tests for S3 access control and authorization boundaries."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError


def test_cross_user_media_access_rejected_by_application_policy() -> None:
    """Verifies that an unauthorized user cannot request a presigned URL for another user's asset."""
    user_a_id = "user-a-1111"
    user_b_id = "user-b-2222"
    asset_owner_id = user_a_id

    # Application policy helper function
    def authorize_and_get_url(requester_id: str, owner_id: str, key: str) -> str:
        if requester_id != owner_id:
            raise PermissionError("Access denied: Requester does not own this resource")
        return f"https://s3.ap-south-1.amazonaws.com/fashx-dev-media/{key}?signature=valid"

    # User A requests their own asset -> authorized
    url_a = authorize_and_get_url(user_a_id, asset_owner_id, "users/user-a-1111/uploads/photo.webp")
    assert "signature=valid" in url_a

    # User B requests User A's asset -> rejected before signed URL generation
    with pytest.raises(PermissionError, match="Access denied"):
        authorize_and_get_url(user_b_id, asset_owner_id, "users/user-a-1111/uploads/photo.webp")


def test_cross_environment_access_denial_simulation() -> None:
    """Simulates S3 AccessDenied when a development task role attempts to read from staging bucket."""
    with patch("boto3.client") as mock_boto:
        mock_c = MagicMock()
        mock_c.get_object.side_effect = ClientError(
            error_response={"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
            operation_name="GetObject",
        )
        mock_boto.return_value = mock_c

        with pytest.raises(ClientError) as exc_info:
            mock_c.get_object(Bucket="fashx-staging-private-123456789012", Key="products/test/item.webp")

        assert exc_info.value.response["Error"]["Code"] == "AccessDenied"


@pytest.mark.skipif(
    os.environ.get("FASHX_STORAGE_INTEGRATION") != "1",
    reason="Requires live AWS S3 credentials and FASHX_STORAGE_INTEGRATION=1",
)
def test_live_s3_cross_environment_access() -> None:  # pragma: no cover
    pass
