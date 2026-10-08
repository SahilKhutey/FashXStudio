"""
Local Filesystem Object Storage Adapter (Rule I10)
"""

import os
from pathlib import Path
from app.application.ports.storage_port import ObjectStoragePort


class LocalStorageAdapter(ObjectStoragePort):
    def __init__(self, base_dir: str = "./storage"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def put(self, path: str, data: bytes, content_type: str = "image/webp") -> str:
        target_path = self.base_dir / path.lstrip("/")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(data)
        return f"file://{target_path.absolute()}"

    async def get_signed_url(self, path: str, expires_in_seconds: int = 900) -> str:
        target_path = self.base_dir / path.lstrip("/")
        return f"http://localhost:8000/storage/{path.lstrip('/')}?token=mock_local_sig"

    async def delete(self, path: str) -> bool:
        target_path = self.base_dir / path.lstrip("/")
        if target_path.exists():
            target_path.unlink()
            return True
        return False

    async def exists(self, path: str) -> bool:
        target_path = self.base_dir / path.lstrip("/")
        return target_path.exists()
