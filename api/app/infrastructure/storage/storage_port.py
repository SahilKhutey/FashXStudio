from abc import ABC, abstractmethod


class StoragePort(ABC):
    @abstractmethod
    async def put(self, path: str, data: bytes, content_type: str = "image/webp") -> str:
        pass

    @abstractmethod
    async def get_signed_url(self, path: str, expires_in_seconds: int = 900) -> str:
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        pass
