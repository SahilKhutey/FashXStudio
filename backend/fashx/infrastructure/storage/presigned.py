from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from fashx.core.settings import get_settings
from fashx.infrastructure.storage.s3 import S3Storage


@dataclass(frozen=True)
class UploadPolicy:
    prefix: str
    max_bytes: int
    allowed_mime_types: tuple[str, ...]


USER_UPLOAD = UploadPolicy(
    prefix="temporary/uploads",
    max_bytes=10 * 1024 * 1024,
    allowed_mime_types=("image/jpeg", "image/png", "image/webp"),
)

PRODUCT_IMAGE_UPLOAD = UploadPolicy(
    prefix="temporary/ingest",
    max_bytes=15 * 1024 * 1024,
    allowed_mime_types=("image/jpeg", "image/png", "image/webp"),
)


def _get_s3_storage() -> S3Storage:
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
    return S3Storage(
        bucket=settings.s3_bucket or "fashx-media",
        endpoint_url=settings.s3_endpoint_url,
        region=settings.s3_region,
        key_id=key_id,
        secret=secret,
        kms_key_id=settings.s3_kms_key_id,
    )


def validate_key(key: str) -> None:
    if not key or key.startswith("/") or ".." in key.split("/"):
        raise ValueError(f"Invalid object key: {key!r}")


def create_upload_session(
    policy: UploadPolicy,
    asset_id: str | None = None,
    ttl_s: int = 300,
) -> dict[str, Any]:
    """Generates a secure presigned POST session for direct browser/client upload to S3."""
    clean_id = asset_id or str(uuid4())
    object_key = f"{policy.prefix}/{clean_id}"
    validate_key(object_key)

    storage = _get_s3_storage()
    post_data = storage.generate_presigned_post(
        key=object_key,
        max_bytes=policy.max_bytes,
        allowed_mime_types=policy.allowed_mime_types,
        ttl_s=ttl_s,
    )

    return {
        "asset_id": clean_id,
        "upload_method": "POST",
        "upload_url": post_data["url"],
        "upload_fields": post_data["fields"],
        "expires_in": ttl_s,
    }


def create_download_url(
    key: str,
    ttl_s: int = 300,
) -> str:
    """Generates a short-lived presigned GET URL for authorized object download.

    Important: This low-level storage helper does NOT perform caller authorization.
    The application layer must verify authenticated user ownership in PostgreSQL before calling.
    """
    validate_key(key)
    storage = _get_s3_storage()
    return storage.signed_get_url(key=key, ttl_s=ttl_s)
