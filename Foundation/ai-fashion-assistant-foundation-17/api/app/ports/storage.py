from __future__ import annotations

from datetime import datetime
from typing import Protocol


class ObjectStoragePort(Protocol):
    def create_upload_url(self, *, key: str, content_type: str, expires_in: int = 900) -> tuple[str, datetime]: ...

    def create_download_url(self, *, key: str, expires_in: int = 900) -> tuple[str, datetime]: ...

    def delete_key(self, *, key: str) -> None: ...

    def head_object(self, *, key: str) -> dict: ...
