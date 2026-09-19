from __future__ import annotations

from hashlib import sha256
from uuid import UUID


def request_fingerprint(*parts: str | int | UUID | None) -> str:
    """Deterministically fingerprint request inputs for idempotency comparisons."""
    canonical = "|".join("" if part is None else str(part) for part in parts)
    return sha256(canonical.encode("utf-8")).hexdigest()
