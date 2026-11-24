"""Virtual Try-On Cache Service.

Coordinates cache lookups, ownership authorization, hit telemetry, and storage.

Architectural Guarantees:
1. Single-user isolation: Results are bound to owner_user_id. A cache hit is only
   valid if record.owner_user_id == requesting_user_id. Cross-user sharing is prohibited.
2. Permission & Takedown Gate: Even on a cache hit, caller/service must verify that
   the merchant garment is not under takedown and shopper consent remains valid.
3. Accurate hit telemetry: Increments hit_count and records last_hit_at for cost analysis.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.fashx.tryon.cache.expiry import (
    get_default_expires_at,
    get_default_metadata_expires_at,
    is_cache_expired,
)
from backend.fashx.tryon.cache.keys import (
    TryOnCacheIdentity,
    compute_cache_key,
    compute_output_options_hash,
)

logger = logging.getLogger(__name__)


class CacheSecurityError(Exception):
    """Raised when an unauthorized user attempts to access a cached result."""


@dataclass
class CacheLookupResult:
    """Represents the outcome of a cache check."""

    hit: bool
    cache_key: str
    result_storage_uri: str | None = None
    result_storage_key: str | None = None
    result_sha256: str | None = None
    source_job_id: UUID | None = None
    created_at: datetime | None = None
    expires_at: datetime | None = None
    hit_count: int = 0
    reason: str | None = None


class TryOnCacheService:
    """Manages cache lifecycle, authorization, and recording."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(
        self,
        identity: TryOnCacheIdentity,
        requesting_user_id: UUID,
    ) -> CacheLookupResult:
        """Look up a cached try-on result with strict owner isolation and validity checks."""
        from database.models.tryon import TryOnResultCache

        cache_key = compute_cache_key(identity)

        # Query cache by key
        stmt = select(TryOnResultCache).where(TryOnResultCache.cache_key == cache_key)
        res = await self.session.execute(stmt)
        record = res.scalar_one_or_none()

        if not record:
            return CacheLookupResult(hit=False, cache_key=cache_key, reason="NOT_FOUND")

        # Invariant 1: Strict Shopper Isolation
        if record.owner_user_id != requesting_user_id:
            logger.error(
                "SECURITY: Cache key collision or access violation! Record owner %s != requesting %s",
                record.owner_user_id,
                requesting_user_id,
            )
            raise CacheSecurityError(
                f"Unauthorized cache access: record owned by {record.owner_user_id}, "
                f"requested by {requesting_user_id}"
            )

        # Invariant 2: Active status
        if record.status != "ACTIVE":
            return CacheLookupResult(
                hit=False,
                cache_key=cache_key,
                reason=f"STATUS_{record.status}",
            )

        # Invariant 3: Expiration
        now = datetime.now(UTC)
        if is_cache_expired(record.expires_at, current_time=now):
            logger.info("Cache entry %s expired at %s", cache_key, record.expires_at)
            # Mark expired in DB
            record.status = "EXPIRED"
            await self.session.flush()
            return CacheLookupResult(hit=False, cache_key=cache_key, reason="EXPIRED")

        # Valid Cache Hit: update hit metrics
        record.hit_count += 1
        record.last_hit_at = now
        await self.session.flush()

        logger.info(
            "Cache HIT for key %s (user %s, hit #%d)",
            cache_key,
            requesting_user_id,
            record.hit_count,
        )

        return CacheLookupResult(
            hit=True,
            cache_key=cache_key,
            result_storage_uri=record.result_storage_uri,
            result_storage_key=record.result_storage_key,
            result_sha256=record.result_sha256,
            source_job_id=record.source_job_id,
            created_at=record.created_at,
            expires_at=record.expires_at,
            hit_count=record.hit_count,
        )

    async def put(
        self,
        identity: TryOnCacheIdentity,
        source_job_id: UUID,
        result_storage_uri: str,
        result_sha256: str,
        result_storage_key: str | None = None,
        shopper_asset_id: UUID | None = None,
        garment_asset_id: UUID | None = None,
    ) -> Any:
        """Store or update a verified try-on result in the cache."""
        from database.models.tryon import TryOnResultCache

        cache_key = compute_cache_key(identity)
        options_hash = compute_output_options_hash(identity.output_options)

        now = datetime.now(UTC)
        expires_at = get_default_expires_at(now)
        metadata_expires_at = get_default_metadata_expires_at(now)

        # Check if record already exists
        stmt = select(TryOnResultCache).where(TryOnResultCache.cache_key == cache_key)
        res = await self.session.execute(stmt)
        record = res.scalar_one_or_none()

        if record:
            # Update existing
            record.result_storage_uri = result_storage_uri
            record.result_storage_key = result_storage_key
            record.result_sha256 = result_sha256
            record.source_job_id = source_job_id
            record.status = "ACTIVE"
            record.invalidation_reason = None
            record.expires_at = expires_at
            record.metadata_expires_at = metadata_expires_at
            record.updated_at = now
        else:
            # Create new entry
            record = TryOnResultCache(
                cache_key=cache_key,
                owner_user_id=identity.user_id,
                canonical_product_id=identity.canonical_product_id,
                shopper_asset_id=shopper_asset_id or identity.user_id,
                shopper_asset_version=identity.shopper_asset_version,
                garment_asset_id=garment_asset_id or identity.canonical_product_id,
                garment_image_version=identity.garment_image_version,
                shopper_image_sha256=identity.shopper_image_sha256.lower(),
                garment_image_sha256=identity.garment_image_sha256.lower(),
                provider=identity.provider.lower().strip(),
                provider_model=identity.provider_model.lower().strip(),
                provider_model_version=identity.provider_model_version.strip(),
                config_version=identity.config_version.strip(),
                preprocessing_version=identity.preprocessing_version.strip(),
                policy_version=identity.policy_version.strip(),
                garment_category=identity.garment_category.lower().strip(),
                output_options_hash=options_hash,
                result_storage_uri=result_storage_uri,
                result_storage_key=result_storage_key,
                result_sha256=result_sha256,
                source_job_id=source_job_id,
                status="ACTIVE",
                hit_count=0,
                expires_at=expires_at,
                metadata_expires_at=metadata_expires_at,
            )
            self.session.add(record)

        await self.session.flush()
        logger.info(
            "Saved try-on result cache key %s for user %s (expires %s)",
            cache_key,
            identity.user_id,
            expires_at,
        )
        return record
