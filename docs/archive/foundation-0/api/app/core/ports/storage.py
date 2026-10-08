from typing import Protocol


class StoragePort(Protocol):
    """Abstract port for object storage (S3 / Cloudflare R2 / local)."""

    async def put(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        """Store binary data under key and return storage key or URI."""
        ...

    async def get(self, key: str) -> bytes | None:
        """Retrieve binary content for key, or None if not found."""
        ...

    async def get_signed_url(self, key: str, expires_in_seconds: int = 900) -> str:
        """Generate ephemeral signed capability URL (default 15 minutes / Rule I07)."""
        ...

    async def delete(self, key: str) -> bool:
        """Delete object at key. Returns True if deleted or already absent."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if key exists in storage."""
        ...


class InMemoryStorageAdapter:
    """In-memory implementation of StoragePort for testing and local development."""

    def __init__(self) -> None:
        self._objects: dict[str, tuple[bytes, str]] = {}

    async def put(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        self._objects[key] = (data, content_type)
        return key

    async def get(self, key: str) -> bytes | None:
        if key in self._objects:
            return self._objects[key][0]
        return None

    async def get_signed_url(self, key: str, expires_in_seconds: int = 900) -> str:
        return f"https://storage.local/{key}?exp={expires_in_seconds}"

    async def delete(self, key: str) -> bool:
        if key in self._objects:
            del self._objects[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        return key in self._objects
