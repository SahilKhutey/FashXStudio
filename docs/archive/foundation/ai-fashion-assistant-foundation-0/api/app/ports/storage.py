from __future__ import annotations

from typing import Protocol


class ObjectStoragePort(Protocol):
    async def create_upload_url(self, *, key: str, content_type: str, expires_in: int = 900) -> str: ...

    async def create_download_url(self, *, key: str, expires_in: int = 3600) -> str: ...

    async def delete_prefix(self, *, prefix: str) -> None: ...
