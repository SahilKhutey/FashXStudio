from __future__ import annotations

from typing import Protocol


class ObjectStorageDownloadPort(Protocol):
    def download_bytes(self, *, key: str) -> bytes: ...
