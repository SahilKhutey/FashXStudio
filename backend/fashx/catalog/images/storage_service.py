"""Private object storage service for catalog image assets and derivatives."""

from __future__ import annotations

import inspect
import os
from typing import Any
from uuid import UUID

from fashx.catalog.images.models import TransformationType


class ImageStorageService:
    """Manages object persistence, path layout, signed URLs, and cleanup compensation."""

    def __init__(self, storage_port: Any, environment: str | None = None) -> None:
        self.storage = storage_port
        self.environment = environment or os.environ.get("ENV", "dev")

    def format_original_key(
        self,
        source_id: UUID,
        asset_id: UUID,
        original_sha256: str,
        extension: str,
    ) -> str:
        """catalog/{env}/sources/{source_id}/originals/{asset_id}/{original_sha256}.{ext}"""
        ext = extension.lstrip(".").lower()
        if ext == "jpeg":
            ext = "jpg"
        return f"catalog/{self.environment}/sources/{source_id}/originals/{asset_id}/{original_sha256}.{ext}"

    def format_display_key(
        self,
        source_id: UUID,
        asset_id: UUID,
        transformation_type: TransformationType | str,
        version: str = "v1",
    ) -> str:
        """catalog/{env}/sources/{source_id}/display/{asset_id}/{version}_{variant}.webp"""
        variant = (
            transformation_type.value
            if hasattr(transformation_type, "value")
            else str(transformation_type)
        ).lower()
        return f"catalog/{self.environment}/sources/{source_id}/display/{asset_id}/{version}_{variant}.webp"

    def format_vto_key(
        self,
        source_id: UUID,
        asset_id: UUID,
        version: str = "v1",
    ) -> str:
        """catalog/{env}/sources/{source_id}/vto/{asset_id}/{version}.png"""
        return f"catalog/{self.environment}/sources/{source_id}/vto/{asset_id}/{version}.png"

    async def put(self, key: str, data: bytes, content_type: str) -> str:
        """Persist bytes to object storage with explicit content type."""
        res = self.storage.put(key, data, content_type=content_type)
        if inspect.isawaitable(res):
            await res
        return key

    async def delete(self, key: str) -> bool:
        """Delete an object from storage; handles both sync and async storage ports."""
        try:
            res = self.storage.delete(key)
            if inspect.isawaitable(res):
                await res
            return True
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        """Check object existence in storage."""
        try:
            res = self.storage.exists(key)
            if inspect.isawaitable(res):
                return bool(await res)
            return bool(res)
        except Exception:
            return False

    async def get_signed_url(self, key: str, expires_in_seconds: int = 900) -> str:
        """Generate short-lived signed URL (default 15 minutes). Never log signed URLs."""
        if hasattr(self.storage, "get_signed_url"):
            res = self.storage.get_signed_url(key, expires_in_seconds=expires_in_seconds)
            if inspect.isawaitable(res):
                return str(await res)
            return str(res)
        if hasattr(self.storage, "signed_get_url"):
            res = self.storage.signed_get_url(key, ttl_s=expires_in_seconds)
            if inspect.isawaitable(res):
                return str(await res)
            return str(res)
        return f"/storage/{key}"
