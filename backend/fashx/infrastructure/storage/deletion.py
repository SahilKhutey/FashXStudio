from __future__ import annotations

import logging
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from fashx.core.settings import get_settings

logger = logging.getLogger(__name__)


def _client() -> Any:
    settings = get_settings()
    key_id = (
        None
        if settings.s3_use_iam_role
        else (
            settings.s3_access_key_id.get_secret_value()
            if settings.s3_access_key_id
            else None
        )
    )
    secret = (
        None
        if settings.s3_use_iam_role
        else (
            settings.s3_secret_access_key.get_secret_value()
            if settings.s3_secret_access_key
            else None
        )
    )
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=key_id,
        aws_secret_access_key=secret,
        config=Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "standard"},
        ),
    )


def validate_key(key: str) -> None:
    if not key or key.startswith("/") or ".." in key.split("/"):
        raise ValueError(f"Invalid object key: {key!r}")


def delete_object(key: str) -> None:
    """Permanently deletes a single S3 object. Idempotent on S3."""
    validate_key(key)
    settings = get_settings()
    bucket = settings.s3_bucket or "fashx-media"
    c = _client()
    c.delete_object(Bucket=bucket, Key=key)
    logger.info("Deleted S3 object %s from bucket %s", key, bucket)


def object_exists(key: str) -> bool:
    """Checks whether an object exists in the S3 bucket using HeadObject.

    Correctly identifies 404 / NoSuchKey vs permission or transport failures.
    """
    validate_key(key)
    settings = get_settings()
    bucket = settings.s3_bucket or "fashx-media"
    c = _client()
    try:
        c.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as exc:
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        code = exc.response.get("Error", {}).get("Code", "")
        if status == 404 or code in ("404", "NoSuchKey", "NotFound"):
            return False
        logger.error("Error inspecting S3 object %s in bucket %s: %s", key, bucket, exc)
        raise


def delete_prefix(prefix: str) -> int:
    """Permanently deletes all S3 objects under a prefix in batches of 1000."""
    validate_key(prefix)
    settings = get_settings()
    bucket = settings.s3_bucket or "fashx-media"
    c = _client()

    deleted_count = 0
    continuation_token = None

    while True:
        params: dict[str, Any] = {"Bucket": bucket, "Prefix": prefix}
        if continuation_token:
            params["ContinuationToken"] = continuation_token

        response = c.list_objects_v2(**params)
        contents = response.get("Contents", [])

        if contents:
            delete_chunk = [{"Key": item["Key"]} for item in contents]
            c.delete_objects(Bucket=bucket, Delete={"Objects": delete_chunk})
            deleted_count += len(delete_chunk)

        if not response.get("IsTruncated"):
            break
        continuation_token = response.get("NextContinuationToken")

    logger.info("Deleted %d objects under prefix %s from bucket %s", deleted_count, prefix, bucket)
    return deleted_count
