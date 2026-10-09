from __future__ import annotations

from typing import Protocol
from uuid import UUID


class ObjectStorage(Protocol):
    """Canonical port for object storage (S3 / Cloudflare R2 / Local)."""

    def put(self, key: str, data: bytes, content_type: str = "image/jpeg") -> None:
        """Store binary object at key with given content type."""
        ...

    def get(self, key: str) -> bytes:
        """Retrieve binary content for key."""
        ...

    def delete(self, key: str) -> None:
        """Delete object at key."""
        ...

    def delete_prefix(self, prefix: str) -> int:
        """Delete all objects matching prefix. Returns count of deleted objects."""
        ...

    def exists(self, key: str) -> bool:
        """Check if object exists at key."""
        ...

    def list_prefix(self, prefix: str) -> list[str]:
        """List all object keys beginning with prefix."""
        ...

    def signed_get_url(self, key: str, ttl_s: int = 300) -> str:
        """Generate expiring signed capability URL for GET access."""
        ...


def media_key(user_id: UUID | str | None, kind: str, media_id: UUID | str | None = None) -> str:
    """Build canonical object key hierarchy for the storage subsystem:
    - Reference user photos: u/<user_id>/photos/<media_id>.jpg
    - Try-on output renders: u/<user_id>/tryon/<job_id>.jpg
    - Catalog garment renders: catalog/garments/<media_id>.jpg
    - Ephemeral scratch files: tmp/<random>.bin
    """
    if kind in ("reference_photo", "photos", "photo"):
        return f"u/{user_id}/photos/{media_id}.jpg"
    elif kind in ("tryon_result", "tryon"):
        return f"u/{user_id}/tryon/{media_id}.jpg"
    elif kind in ("tmp", "scratch"):
        return f"tmp/{media_id}.bin"
    elif kind in ("garment_render", "catalog"):
        return f"catalog/garments/{media_id}.jpg"
    else:
        if user_id:
            return f"u/{user_id}/{kind}/{media_id}.jpg"
        return f"{kind}/{media_id}.jpg"
