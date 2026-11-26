"""Virtual Try-On Cache Module."""

from fashx.tryon.cache.expiry import (
    DEFAULT_CACHE_TTL_DAYS,
    DEFAULT_METADATA_RETENTION_DAYS,
    get_default_expires_at,
    get_default_metadata_expires_at,
    is_cache_expired,
    is_metadata_expired,
)
from fashx.tryon.cache.invalidation import (
    CacheInvalidationService,
    InvalidationReason,
)
from fashx.tryon.cache.keys import (
    TryOnCacheIdentity,
    compute_cache_key,
    compute_output_options_hash,
)
from fashx.tryon.cache.service import (
    CacheLookupResult,
    CacheSecurityError,
    TryOnCacheService,
)

__all__ = [
    "DEFAULT_CACHE_TTL_DAYS",
    "DEFAULT_METADATA_RETENTION_DAYS",
    "get_default_expires_at",
    "get_default_metadata_expires_at",
    "is_cache_expired",
    "is_metadata_expired",
    "CacheInvalidationService",
    "InvalidationReason",
    "TryOnCacheIdentity",
    "compute_cache_key",
    "compute_output_options_hash",
    "CacheLookupResult",
    "CacheSecurityError",
    "TryOnCacheService",
]
