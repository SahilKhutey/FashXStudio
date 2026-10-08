from __future__ import annotations

from typing import Protocol
from uuid import UUID


class CatalogPort(Protocol):
    async def get_garment(self, garment_id: UUID) -> dict: ...
