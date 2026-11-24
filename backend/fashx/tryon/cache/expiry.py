"""Cache TTL and retention calculations for Virtual Try-On results.

Standard Policies:
1. Result Image TTL: 7 days. After 7 days, underlying generated images stored
   in private object storage are deleted or expired to control storage costs.
2. Result Metadata Retention: 30 days. Ledger records, hit counts, and performance
   telemetry are preserved for 30 days before full archival/pruning.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

DEFAULT_CACHE_TTL_DAYS = 7
DEFAULT_METADATA_RETENTION_DAYS = 30


def get_default_expires_at(from_time: datetime | None = None) -> datetime:
    """Calculate the expiration datetime for a cached result image (7 days)."""
    base = from_time or datetime.now(UTC)
    return base + timedelta(days=DEFAULT_CACHE_TTL_DAYS)


def get_default_metadata_expires_at(from_time: datetime | None = None) -> datetime:
    """Calculate the retention datetime for cache metadata (30 days)."""
    base = from_time or datetime.now(UTC)
    return base + timedelta(days=DEFAULT_METADATA_RETENTION_DAYS)


def is_cache_expired(expires_at: datetime, current_time: datetime | None = None) -> bool:
    """Check if the cache entry has passed its image expiration time."""
    now = current_time or datetime.now(UTC)
    # Ensure timezone awareness
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    return now >= expires_at


def is_metadata_expired(
    metadata_expires_at: datetime, current_time: datetime | None = None
) -> bool:
    """Check if the cache record metadata has exceeded its 30-day retention limit."""
    now = current_time or datetime.now(UTC)
    if metadata_expires_at.tzinfo is None:
        metadata_expires_at = metadata_expires_at.replace(tzinfo=UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    return now >= metadata_expires_at
