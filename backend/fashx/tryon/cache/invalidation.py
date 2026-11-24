"""Cache invalidation engine for Virtual Try-On results.

Handles deterministic invalidation across:
1. Merchant product image revision change
2. Merchant product takedown or catalog delisting
3. Shopper consent revocation or GDPR/CCPA deletion
4. Provider model upgrade or quality policy deprecation
5. Administrative purge
"""

from __future__ import annotations

import logging
from enum import Enum
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class InvalidationReason(str, Enum):
    PRODUCT_IMAGE_CHANGED = "PRODUCT_IMAGE_CHANGED"
    PRODUCT_TAKEDOWN = "PRODUCT_TAKEDOWN"
    MERCHANT_DELISTED = "MERCHANT_DELISTED"
    CONSENT_WITHDRAWN = "CONSENT_WITHDRAWN"
    SHOPPER_DELETED = "SHOPPER_DELETED"
    PROVIDER_CONFIG_CHANGED = "PROVIDER_CONFIG_CHANGED"
    POLICY_VERSION_BUMPED = "POLICY_VERSION_BUMPED"
    MANUAL_PURGE = "MANUAL_PURGE"


class CacheInvalidationService:
    """Service for managing invalidation of try-on result cache entries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def invalidate_by_product_id(
        self,
        canonical_product_id: UUID,
        reason: InvalidationReason,
        details: str | None = None,
    ) -> int:
        """Invalidate all active cache entries associated with a product."""
        # Lazy import of model to prevent circular dependency
        from database.models.tryon import TryOnResultCache

        invalidation_text = f"{reason.value}: {details}" if details else reason.value
        stmt = (
            update(TryOnResultCache)
            .where(
                TryOnResultCache.canonical_product_id == canonical_product_id,
                TryOnResultCache.status == "ACTIVE",
            )
            .values(
                status="INVALIDATED",
                invalidation_reason=invalidation_text,
            )
        )
        result = await self.session.execute(stmt)
        count = result.rowcount  # type: ignore[attr-defined]
        logger.info(
            "Invalidated %d cache entries for product %s (reason: %s)",
            count,
            canonical_product_id,
            reason.value,
        )
        return count

    async def invalidate_by_user_id(
        self,
        owner_user_id: UUID,
        reason: InvalidationReason,
        details: str | None = None,
    ) -> int:
        """Invalidate all active cache entries owned by a user (e.g. consent withdrawal)."""
        from database.models.tryon import TryOnResultCache

        invalidation_text = f"{reason.value}: {details}" if details else reason.value
        stmt = (
            update(TryOnResultCache)
            .where(
                TryOnResultCache.owner_user_id == owner_user_id,
                TryOnResultCache.status == "ACTIVE",
            )
            .values(
                status="INVALIDATED",
                invalidation_reason=invalidation_text,
            )
        )
        result = await self.session.execute(stmt)
        count = result.rowcount  # type: ignore[attr-defined]
        logger.info(
            "Invalidated %d cache entries for user %s (reason: %s)",
            count,
            owner_user_id,
            reason.value,
        )
        return count

    async def invalidate_by_cache_key(
        self,
        cache_key: str,
        reason: InvalidationReason,
        details: str | None = None,
    ) -> bool:
        """Invalidate a specific cache key."""
        from database.models.tryon import TryOnResultCache

        invalidation_text = f"{reason.value}: {details}" if details else reason.value
        stmt = (
            update(TryOnResultCache)
            .where(
                TryOnResultCache.cache_key == cache_key,
                TryOnResultCache.status == "ACTIVE",
            )
            .values(
                status="INVALIDATED",
                invalidation_reason=invalidation_text,
            )
        )
        result = await self.session.execute(stmt)
        count = result.rowcount  # type: ignore[attr-defined]
        return count > 0

    async def invalidate_by_provider_model(
        self,
        provider: str,
        provider_model: str,
        reason: InvalidationReason,
        details: str | None = None,
    ) -> int:
        """Invalidate cache entries for a deprecated provider model version."""
        from database.models.tryon import TryOnResultCache

        invalidation_text = f"{reason.value}: {details}" if details else reason.value
        stmt = (
            update(TryOnResultCache)
            .where(
                TryOnResultCache.provider == provider,
                TryOnResultCache.provider_model == provider_model,
                TryOnResultCache.status == "ACTIVE",
            )
            .values(
                status="INVALIDATED",
                invalidation_reason=invalidation_text,
            )
        )
        result = await self.session.execute(stmt)
        count = result.rowcount  # type: ignore[attr-defined]
        return count
