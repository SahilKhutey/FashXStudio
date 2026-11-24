"""Unit tests for TryOnCacheService, owner isolation, and invalidation (Phase 07.6).

Covers CACHE-SVC-001 through CACHE-SVC-007.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.fashx.tryon.cache.invalidation import (
    CacheInvalidationService,
    InvalidationReason,
)
from backend.fashx.tryon.cache.keys import (
    TryOnCacheIdentity,
    compute_cache_key,
)
from backend.fashx.tryon.cache.service import (
    CacheSecurityError,
    TryOnCacheService,
)

SAMPLE_USER_A = uuid.UUID("11111111-1111-4111-8111-111111111111")
SAMPLE_USER_B = uuid.UUID("22222222-2222-4222-8222-222222222222")
SAMPLE_PRODUCT_ID = uuid.UUID("33333333-3333-4333-8333-333333333333")
SAMPLE_JOB_ID = uuid.UUID("55555555-5555-4555-8555-555555555555")
SAMPLE_HASH_1 = "1" * 64
SAMPLE_HASH_2 = "2" * 64


def make_identity(user_id: uuid.UUID = SAMPLE_USER_A) -> TryOnCacheIdentity:
    return TryOnCacheIdentity(
        user_id=user_id,
        canonical_product_id=SAMPLE_PRODUCT_ID,
        shopper_image_sha256=SAMPLE_HASH_1,
        garment_image_sha256=SAMPLE_HASH_2,
        shopper_asset_version=1,
        garment_image_version=1,
        provider="fashn",
        provider_model="tryon-v1.6",
        provider_model_version="2026.1",
        config_version="v1.0",
        preprocessing_version="prep-v1",
        policy_version="policy-2026",
        garment_category="tops",
        output_options={},
    )


class MockCacheRecord:
    def __init__(
        self,
        cache_key: str,
        owner_user_id: uuid.UUID,
        status: str = "ACTIVE",
        expires_at: datetime | None = None,
    ):
        self.id = uuid.uuid4()
        self.cache_key = cache_key
        self.owner_user_id = owner_user_id
        self.status = status
        self.expires_at = expires_at or (datetime.now(UTC) + timedelta(days=7))
        self.result_storage_uri = "s3://private-bucket/tryon/result.jpg"
        self.result_storage_key = "tryon/result.jpg"
        self.result_sha256 = "f" * 64
        self.source_job_id = SAMPLE_JOB_ID
        self.hit_count = 0
        self.last_hit_at = None
        self.created_at = datetime.now(UTC)


@pytest.mark.asyncio
async def test_cache_miss_when_not_found():
    """CACHE-SVC-001: Returns hit=False when key does not exist."""
    session = AsyncMock()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = None
    session.execute.return_value = exec_result

    service = TryOnCacheService(session)
    identity = make_identity()
    result = await service.get(identity, requesting_user_id=SAMPLE_USER_A)

    assert result.hit is False
    assert result.reason == "NOT_FOUND"


@pytest.mark.asyncio
async def test_cache_hit_authorized_owner():
    """CACHE-SVC-002: Returns hit=True when key exists and requesting user is owner."""
    session = AsyncMock()
    identity = make_identity()
    key = compute_cache_key(identity)
    record = MockCacheRecord(cache_key=key, owner_user_id=SAMPLE_USER_A)

    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = record
    session.execute.return_value = exec_result

    service = TryOnCacheService(session)
    result = await service.get(identity, requesting_user_id=SAMPLE_USER_A)

    assert result.hit is True
    assert result.result_storage_uri == record.result_storage_uri
    assert record.hit_count == 1
    assert record.last_hit_at is not None


@pytest.mark.asyncio
async def test_cache_security_violation_raises():
    """CACHE-SVC-003: Raises CacheSecurityError if requesting user does not match owner."""
    session = AsyncMock()
    identity = make_identity(user_id=SAMPLE_USER_A)
    key = compute_cache_key(identity)
    # Record owned by User A
    record = MockCacheRecord(cache_key=key, owner_user_id=SAMPLE_USER_A)

    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = record
    session.execute.return_value = exec_result

    service = TryOnCacheService(session)
    with pytest.raises(CacheSecurityError, match="Unauthorized cache access"):
        await service.get(identity, requesting_user_id=SAMPLE_USER_B)


@pytest.mark.asyncio
async def test_cache_miss_when_expired():
    """CACHE-SVC-004: Returns hit=False (reason=EXPIRED) when entry has passed TTL."""
    session = AsyncMock()
    identity = make_identity()
    key = compute_cache_key(identity)
    # Expired 1 hour ago
    past_expiry = datetime.now(UTC) - timedelta(hours=1)
    record = MockCacheRecord(cache_key=key, owner_user_id=SAMPLE_USER_A, expires_at=past_expiry)

    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = record
    session.execute.return_value = exec_result

    service = TryOnCacheService(session)
    result = await service.get(identity, requesting_user_id=SAMPLE_USER_A)

    assert result.hit is False
    assert result.reason == "EXPIRED"
    assert record.status == "EXPIRED"


@pytest.mark.asyncio
async def test_cache_miss_when_invalidated():
    """CACHE-SVC-005: Returns hit=False when status is INVALIDATED."""
    session = AsyncMock()
    identity = make_identity()
    key = compute_cache_key(identity)
    record = MockCacheRecord(cache_key=key, owner_user_id=SAMPLE_USER_A, status="INVALIDATED")

    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = record
    session.execute.return_value = exec_result

    service = TryOnCacheService(session)
    result = await service.get(identity, requesting_user_id=SAMPLE_USER_A)

    assert result.hit is False
    assert result.reason == "STATUS_INVALIDATED"


@pytest.mark.asyncio
async def test_invalidation_by_product():
    """CACHE-SVC-006: Invalidation service updates product records."""
    session = AsyncMock()
    exec_result = MagicMock()
    exec_result.rowcount = 4
    session.execute.return_value = exec_result

    invalidator = CacheInvalidationService(session)
    count = await invalidator.invalidate_by_product_id(
        SAMPLE_PRODUCT_ID,
        InvalidationReason.PRODUCT_TAKEDOWN,
        details="DMCA takedown notice #1042",
    )
    assert count == 4
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_invalidation_by_user_consent():
    """CACHE-SVC-007: Invalidation service updates user records on consent withdrawal."""
    session = AsyncMock()
    exec_result = MagicMock()
    exec_result.rowcount = 2
    session.execute.return_value = exec_result

    invalidator = CacheInvalidationService(session)
    count = await invalidator.invalidate_by_user_id(
        SAMPLE_USER_A,
        InvalidationReason.CONSENT_WITHDRAWN,
        details="User revoked photo consent",
    )
    assert count == 2
    session.execute.assert_called_once()
