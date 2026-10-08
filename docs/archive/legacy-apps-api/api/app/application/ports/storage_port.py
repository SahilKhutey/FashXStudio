"""
Abstract Object Storage Port (Rule I10)
Decouples application use cases from S3, R2, or local storage.
"""

from abc import ABC, abstractmethod
from typing import Optional


class ObjectStoragePort(ABC):
    @abstractmethod
    async def put(self, path: str, data: bytes, content_type: str = "image/webp") -> str:
        """Uploads binary data and returns the canonical storage URI."""
        pass

    @abstractmethod
    async def get_signed_url(self, path: str, expires_in_seconds: int = 900) -> str:
        """Generates a short-lived presigned URL for read access."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Performs a hard deletion of the object."""
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Checks if the object exists in storage."""
        pass
