"""Session-based feed candidate caching for stable pagination and fast recall (Step 7.15)."""

import time
from uuid import UUID

# In-memory session candidate storage with TTL
_MEMORY_CACHE: dict[str, tuple[list[str], float]] = {}
CACHE_TTL_SECONDS = 900.0  # 15 minutes


def _clean_expired_cache() -> None:
    now = time.time()
    expired = [k for k, (_, exp) in _MEMORY_CACHE.items() if exp < now]
    for k in expired:
        _MEMORY_CACHE.pop(k, None)


def get_cached_candidate_ids(user_id: UUID | str, session_id: str) -> list[str] | None:
    """Retrieve cached candidate IDs for a user session if valid and not expired."""
    _clean_expired_cache()
    key = f"feed:{user_id}:{session_id}"
    item = _MEMORY_CACHE.get(key)
    if item is None:
        return None
    ids, exp = item
    if time.time() > exp:
        _MEMORY_CACHE.pop(key, None)
        return None
    return list(ids)


def set_cached_candidate_ids(
    user_id: UUID | str, session_id: str, candidate_ids: list[str], ttl: float = CACHE_TTL_SECONDS
) -> None:
    """Store candidate IDs for a session with a 15-minute TTL."""
    key = f"feed:{user_id}:{session_id}"
    exp = time.time() + ttl
    _MEMORY_CACHE[key] = (list(candidate_ids), exp)


def invalidate_user_cache(user_id: UUID | str) -> int:
    """Invalidate all active feed sessions for a user upon receiving new positive signals."""
    prefix = f"feed:{user_id}:"
    matching = [k for k in _MEMORY_CACHE if k.startswith(prefix)]
    for k in matching:
        _MEMORY_CACHE.pop(k, None)
    return len(matching)
