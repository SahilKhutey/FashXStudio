from pathlib import Path
from api.app.infrastructure.storage.storage_port import StoragePort


class R2StorageAdapter(StoragePort):
    def __init__(self, bucket_name: str = "fashx-media", local_dir: str = "./storage"):
        self.bucket_name = bucket_name
        self.local_dir = Path(local_dir)
        self.local_dir.mkdir(parents=True, exist_ok=True)

    async def put(self, path: str, data: bytes, content_type: str = "image/webp") -> str:
        target = self.local_dir / path.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return f"r2://{self.bucket_name}/{path.lstrip('/')}"

    async def get_signed_url(self, path: str, expires_in_seconds: int = 900) -> str:
        return f"https://media.fashx.studio/{path.lstrip('/')}?token=mock_signed_token"

    async def delete(self, path: str) -> bool:
        target = self.local_dir / path.lstrip("/")
        if target.exists():
            target.unlink()
            return True
        return False

    async def exists(self, path: str) -> bool:
        target = self.local_dir / path.lstrip("/")
        return target.exists()
