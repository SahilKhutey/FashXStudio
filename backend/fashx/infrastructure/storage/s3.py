from __future__ import annotations

import time
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from fashx.core.metrics import emit_metric


class S3Storage:
    """S3-compatible object storage adapter supporting AWS S3 and Cloudflare R2."""

    def __init__(
        self,
        bucket: str,
        endpoint_url: str | None = None,
        region: str = "auto",
        key_id: str | None = None,
        secret: str | None = None,
        kms_key_id: str | None = None,
        environment: str = "dev",
    ) -> None:
        self._b = bucket
        self._is_aws = endpoint_url is None
        self._kms_key_id = kms_key_id
        self._env = environment
        self._c = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=key_id,
            aws_secret_access_key=secret,
            config=Config(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )

    @staticmethod
    def _validate_key(key: str) -> None:
        if not key or key.startswith("/") or ".." in key.split("/"):
            raise ValueError(f"Invalid object key: {key!r}")

    def put(
        self, key: str, data: bytes, content_type: str = "image/jpeg"
    ) -> None:
        self._validate_key(key)
        kwargs: dict[str, Any] = {
            "Bucket": self._b,
            "Key": key,
            "Body": data,
            "ContentType": content_type,
        }
        if self._is_aws:
            if self._kms_key_id:
                kwargs["ServerSideEncryption"] = "aws:kms"
                kwargs["SSEKMSKeyId"] = self._kms_key_id
            else:
                kwargs["ServerSideEncryption"] = "AES256"

        started = time.perf_counter()
        try:
            self._c.put_object(**kwargs)
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            emit_metric("StorageUploadCount", 1.0, "Count", service="storage", environment=self._env, dimensions={"Operation": "put", "Outcome": "success"}, namespace="FashX/Storage")
            emit_metric("StorageBytesUploaded", float(len(data)), "Bytes", service="storage", environment=self._env, dimensions={"Operation": "put"}, namespace="FashX/Storage")
            emit_metric("StorageOperationLatency", duration_ms, "Milliseconds", service="storage", environment=self._env, dimensions={"Operation": "put", "Outcome": "success"}, namespace="FashX/Storage")
        except Exception:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            emit_metric("StorageUploadErrors", 1.0, "Count", service="storage", environment=self._env, dimensions={"Operation": "put", "Outcome": "failure"}, namespace="FashX/Storage")
            emit_metric("StorageOperationLatency", duration_ms, "Milliseconds", service="storage", environment=self._env, dimensions={"Operation": "put", "Outcome": "failure"}, namespace="FashX/Storage")
            raise

    def get(self, key: str) -> bytes:
        self._validate_key(key)
        started = time.perf_counter()
        try:
            body = self._c.get_object(Bucket=self._b, Key=key)["Body"].read()
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            emit_metric("StorageDownloadCount", 1.0, "Count", service="storage", environment=self._env, dimensions={"Operation": "get", "Outcome": "success"}, namespace="FashX/Storage")
            emit_metric("StorageBytesDownloaded", float(len(body)), "Bytes", service="storage", environment=self._env, dimensions={"Operation": "get"}, namespace="FashX/Storage")
            emit_metric("StorageOperationLatency", duration_ms, "Milliseconds", service="storage", environment=self._env, dimensions={"Operation": "get", "Outcome": "success"}, namespace="FashX/Storage")
            return body
        except Exception:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            emit_metric("StorageDownloadErrors", 1.0, "Count", service="storage", environment=self._env, dimensions={"Operation": "get", "Outcome": "failure"}, namespace="FashX/Storage")
            emit_metric("StorageOperationLatency", duration_ms, "Milliseconds", service="storage", environment=self._env, dimensions={"Operation": "get", "Outcome": "failure"}, namespace="FashX/Storage")
            raise

    def head(self, key: str) -> dict[str, Any]:
        self._validate_key(key)
        return self._c.head_object(Bucket=self._b, Key=key)

    def copy(self, src_key: str, dst_key: str) -> None:
        self._validate_key(src_key)
        self._validate_key(dst_key)
        copy_source = {"Bucket": self._b, "Key": src_key}
        kwargs: dict[str, Any] = {
            "Bucket": self._b,
            "CopySource": copy_source,
            "Key": dst_key,
        }
        if self._is_aws:
            if self._kms_key_id:
                kwargs["ServerSideEncryption"] = "aws:kms"
                kwargs["SSEKMSKeyId"] = self._kms_key_id
            else:
                kwargs["ServerSideEncryption"] = "AES256"
        self._c.copy_object(**kwargs)

    def delete(self, key: str) -> None:
        self._validate_key(key)
        started = time.perf_counter()
        try:
            self._c.delete_object(Bucket=self._b, Key=key)
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            emit_metric("StorageDeleteCount", 1.0, "Count", service="storage", environment=self._env, dimensions={"Operation": "delete", "Outcome": "success"}, namespace="FashX/Storage")
            emit_metric("StorageOperationLatency", duration_ms, "Milliseconds", service="storage", environment=self._env, dimensions={"Operation": "delete", "Outcome": "success"}, namespace="FashX/Storage")
        except Exception:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            emit_metric("StorageDeleteErrors", 1.0, "Count", service="storage", environment=self._env, dimensions={"Operation": "delete", "Outcome": "failure"}, namespace="FashX/Storage")
            emit_metric("StorageOperationLatency", duration_ms, "Milliseconds", service="storage", environment=self._env, dimensions={"Operation": "delete", "Outcome": "failure"}, namespace="FashX/Storage")
            raise

    def exists(self, key: str) -> bool:
        self._validate_key(key)
        try:
            self._c.head_object(Bucket=self._b, Key=key)
            return True
        except ClientError as e:
            status = (
                e.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            )
            code = e.response.get("Error", {}).get("Code", "")
            if status == 404 or code in ("404", "NoSuchKey", "NotFound"):
                return False
            raise

    def list_prefix(self, prefix: str) -> list[str]:
        out: list[str] = []
        tok = None
        while True:
            params: dict[str, str] = {"Bucket": self._b, "Prefix": prefix}
            if tok:
                params["ContinuationToken"] = tok
            r = self._c.list_objects_v2(**params)
            out.extend([o["Key"] for o in r.get("Contents", [])])
            if not r.get("IsTruncated"):
                return out
            tok = r.get("NextContinuationToken")

    def delete_prefix(self, prefix: str) -> int:
        keys = self.list_prefix(prefix)
        for i in range(0, len(keys), 1000):
            chunk = [{"Key": k} for k in keys[i : i + 1000]]
            self._c.delete_objects(Bucket=self._b, Delete={"Objects": chunk})
        return len(keys)

    def signed_get_url(self, key: str, ttl_s: int = 300) -> str:
        self._validate_key(key)
        return self._c.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._b, "Key": key},
            ExpiresIn=ttl_s,
        )

    def generate_presigned_post(
        self,
        key: str,
        max_bytes: int,
        allowed_mime_types: tuple[str, ...],
        ttl_s: int = 300,
    ) -> dict[str, Any]:
        self._validate_key(key)
        fields: dict[str, str] = {}
        conditions: list[Any] = [
            ["content-length-range", 1, max_bytes],
        ]
        if allowed_mime_types:
            if len(allowed_mime_types) == 1:
                fields["Content-Type"] = allowed_mime_types[0]
                conditions.append({"Content-Type": allowed_mime_types[0]})
            else:
                conditions.append(["starts-with", "$Content-Type", "image/"])

        if self._is_aws:
            if self._kms_key_id:
                fields["x-amz-server-side-encryption"] = "aws:kms"
                fields["x-amz-server-side-encryption-aws-kms-key-id"] = (
                    self._kms_key_id
                )
                conditions.append({"x-amz-server-side-encryption": "aws:kms"})
                conditions.append(
                    {
                        "x-amz-server-side-encryption-aws-kms-key-id": (
                            self._kms_key_id
                        )
                    }
                )
            else:
                fields["x-amz-server-side-encryption"] = "AES256"
                conditions.append({"x-amz-server-side-encryption": "AES256"})

        return self._c.generate_presigned_post(
            Bucket=self._b,
            Key=key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=ttl_s,
        )
