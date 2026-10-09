from __future__ import annotations

import hashlib
import hmac
import os
import time
from pathlib import Path


class LocalStorage:
    """Local filesystem storage adapter for development and testing. Refuses ENV=prod."""

    def __init__(self, root_dir: str | Path = "./.local_storage", base_url: str = "http://127.0.0.1:8000") -> None:
        if os.environ.get("ENV") == "prod":
            raise RuntimeError("LocalStorage cannot be used in production (ENV=prod)")
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url.rstrip("/")

    def put(self, key: str, data: bytes, content_type: str = "image/jpeg") -> None:
        target = self.root / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def get(self, key: str) -> bytes:
        target = self.root / key
        if not target.exists():
            raise FileNotFoundError(f"Key not found: {key}")
        return target.read_bytes()

    def delete(self, key: str) -> None:
        target = self.root / key
        if target.exists():
            target.unlink()

    def exists(self, key: str) -> bool:
        return (self.root / key).is_file()

    def list_prefix(self, prefix: str) -> list[str]:
        prefix_clean = prefix.lstrip("/")
        if not self.root.exists():
            return []
        keys = [
            p.relative_to(self.root).as_posix()
            for p in self.root.rglob("*")
            if p.is_file() and p.relative_to(self.root).as_posix().startswith(prefix_clean)
        ]
        return sorted(keys)

    def delete_prefix(self, prefix: str) -> int:
        keys = self.list_prefix(prefix)
        for k in keys:
            (self.root / k).unlink(missing_ok=True)
        return len(keys)

    def signed_get_url(self, key: str, ttl_s: int = 300) -> str:
        exp = int(time.time()) + ttl_s
        sig = hmac.new(b"dev-secret", f"{key}:{exp}".encode(), hashlib.sha256).hexdigest()[:16]
        return f"{self.base_url}/dev-files/{key}?exp={exp}&sig={sig}"
