from __future__ import annotations

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class S3Storage:
    """S3-compatible object storage adapter supporting AWS S3 and Cloudflare R2."""

    def __init__(
        self,
        bucket: str,
        endpoint_url: str | None = None,
        region: str = "auto",
        key_id: str | None = None,
        secret: str | None = None,
    ) -> None:
        self._b = bucket
        self._is_aws = endpoint_url is None
        self._c = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=key_id,
            aws_secret_access_key=secret,
            config=Config(signature_version="s3v4", retries={"max_attempts": 3, "mode": "standard"}),
        )

    def put(self, key: str, data: bytes, content_type: str = "image/jpeg") -> None:
        if self._is_aws:
            self._c.put_object(
                Bucket=self._b,
                Key=key,
                Body=data,
                ContentType=content_type,
                ServerSideEncryption="AES256",
            )
        else:
            self._c.put_object(
                Bucket=self._b,
                Key=key,
                Body=data,
                ContentType=content_type,
            )

    def get(self, key: str) -> bytes:
        return self._c.get_object(Bucket=self._b, Key=key)["Body"].read()

    def delete(self, key: str) -> None:
        self._c.delete_object(Bucket=self._b, Key=key)

    def exists(self, key: str) -> bool:
        try:
            self._c.head_object(Bucket=self._b, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
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
        return self._c.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._b, "Key": key},
            ExpiresIn=ttl_s,
        )
