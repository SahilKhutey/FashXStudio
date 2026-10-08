from __future__ import annotations

from typing import Protocol
from uuid import UUID


class ProfilePort(Protocol):
    async def get_derived(self, user_id: UUID) -> dict: ...

    async def issue_media_capability(self, *, user_id: UUID, photo_id: UUID, purpose: str, job_id: UUID) -> str: ...
