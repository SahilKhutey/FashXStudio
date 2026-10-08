from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID


class ProfileMediaPort(Protocol):
    async def get_scoped_download_url(
        self, *, user_id: UUID, photo_id: UUID, purpose: str, job_id: UUID
    ) -> tuple[str, datetime]: ...
