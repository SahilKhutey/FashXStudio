from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import boto3
from botocore.client import Config as BotoConfig

from api.app.core.settings import get_settings


class R2StorageClient:
    def __init__(self) -> None:
        settings = get_settings()
        if not all([settings.r2_endpoint_url, settings.r2_access_key_id, settings.r2_secret_access_key, settings.r2_bucket]):
            raise RuntimeError("R2 storage is not configured")
        self.bucket = settings.r2_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name=settings.r2_region,
            config=BotoConfig(signature_version="s3v4"),
        )

    def create_upload_url(self, *, key: str, content_type: str, expires_in: int = 900) -> tuple[str, datetime]:
        url = self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_in,
        )
        return url, datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    def create_download_url(self, *, key: str, expires_in: int = 900) -> tuple[str, datetime]:
        url = self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return url, datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    def delete_key(self, *, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def download_bytes(self, *, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        body = response["Body"]
        try:
            return body.read()
        finally:
            body.close()

    def head_object(self, *, key: str) -> dict:
        return self.client.head_object(Bucket=self.bucket, Key=key)
