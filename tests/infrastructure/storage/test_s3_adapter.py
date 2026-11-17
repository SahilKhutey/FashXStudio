"""Unit tests for the enhanced S3Storage adapter class."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from fashx.infrastructure.storage.s3 import S3Storage


def test_s3_storage_put_with_kms_key() -> None:
    with patch("boto3.client") as mock_boto:
        mock_c = MagicMock()
        mock_boto.return_value = mock_c

        storage = S3Storage(
            bucket="fashx-prod-private",
            region="ap-south-1",
            kms_key_id="arn:aws:kms:ap-south-1:123456789012:key/test-kms-key",
        )

        storage.put("tryon/user-1/job-1/result.webp", b"imagedata", content_type="image/webp")

        mock_c.put_object.assert_called_once()
        _, kwargs = mock_c.put_object.call_args
        assert kwargs["Bucket"] == "fashx-prod-private"
        assert kwargs["Key"] == "tryon/user-1/job-1/result.webp"
        assert kwargs["ServerSideEncryption"] == "aws:kms"
        assert kwargs["SSEKMSKeyId"] == "arn:aws:kms:ap-south-1:123456789012:key/test-kms-key"


def test_s3_storage_put_fallback_aes256() -> None:
    with patch("boto3.client") as mock_boto:
        mock_c = MagicMock()
        mock_boto.return_value = mock_c

        storage = S3Storage(
            bucket="fashx-dev-private",
            region="ap-south-1",
            kms_key_id=None,
        )

        storage.put("products/m1/p1/asset.webp", b"data", content_type="image/webp")

        mock_c.put_object.assert_called_once()
        _, kwargs = mock_c.put_object.call_args
        assert kwargs["ServerSideEncryption"] == "AES256"


def test_s3_storage_copy_and_head() -> None:
    with patch("boto3.client") as mock_boto:
        mock_c = MagicMock()
        mock_c.head_object.return_value = {"ContentLength": 5000, "ContentType": "image/webp"}
        mock_boto.return_value = mock_c

        storage = S3Storage(
            bucket="fashx-dev-private",
            region="ap-south-1",
            kms_key_id="test-key",
        )

        head_res = storage.head("products/m1/p1/asset.webp")
        assert head_res["ContentLength"] == 5000

        storage.copy("temporary/uploads/temp-1.webp", "users/u1/uploads/photo.webp")
        mock_c.copy_object.assert_called_once()
        _, kwargs = mock_c.copy_object.call_args
        assert kwargs["CopySource"] == {"Bucket": "fashx-dev-private", "Key": "temporary/uploads/temp-1.webp"}
        assert kwargs["Key"] == "users/u1/uploads/photo.webp"
        assert kwargs["ServerSideEncryption"] == "aws:kms"


def test_s3_storage_generate_presigned_post_with_kms() -> None:
    with patch("boto3.client") as mock_boto:
        mock_c = MagicMock()
        mock_c.generate_presigned_post.return_value = {
            "url": "https://s3.ap-south-1.amazonaws.com/fashx-prod-private",
            "fields": {"key": "temporary/uploads/u1"},
        }
        mock_boto.return_value = mock_c

        storage = S3Storage(
            bucket="fashx-prod-private",
            region="ap-south-1",
            kms_key_id="test-kms-arn",
        )

        res = storage.generate_presigned_post(
            key="temporary/uploads/u1",
            max_bytes=10 * 1024 * 1024,
            allowed_mime_types=("image/jpeg", "image/png"),
            ttl_s=300,
        )

        assert res["url"] == "https://s3.ap-south-1.amazonaws.com/fashx-prod-private"
        mock_c.generate_presigned_post.assert_called_once()
        _, kwargs = mock_c.generate_presigned_post.call_args
        assert kwargs["Key"] == "temporary/uploads/u1"
        assert kwargs["Fields"]["x-amz-server-side-encryption"] == "aws:kms"
        assert kwargs["Fields"]["x-amz-server-side-encryption-aws-kms-key-id"] == "test-kms-arn"


def test_s3_storage_rejects_malformed_key() -> None:
    with patch("boto3.client"):
        storage = S3Storage(bucket="test-bucket")
        with pytest.raises(ValueError, match="Invalid object key"):
            storage.put("/leading/slash.jpg", b"data")
        with pytest.raises(ValueError, match="Invalid object key"):
            storage.get("../traversal.jpg")
        with pytest.raises(ValueError, match="Invalid object key"):
            storage.delete("")
