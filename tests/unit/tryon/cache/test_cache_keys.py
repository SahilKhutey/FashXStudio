"""Unit tests for deterministic TryOnCacheIdentity and key generation (Phase 07.6).

Covers CACHE-001 through CACHE-020.
"""

from __future__ import annotations

import uuid

import pytest

from backend.fashx.tryon.cache.keys import (
    TryOnCacheIdentity,
    compute_cache_key,
)

SAMPLE_USER_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")
OTHER_USER_ID = uuid.UUID("22222222-2222-4222-8222-222222222222")
SAMPLE_PRODUCT_ID = uuid.UUID("33333333-3333-4333-8333-333333333333")
OTHER_PRODUCT_ID = uuid.UUID("44444444-4444-4444-8444-444444444444")
SAMPLE_HASH_1 = "a" * 64
SAMPLE_HASH_2 = "b" * 64
SAMPLE_HASH_3 = "c" * 64


def create_base_identity(**overrides) -> TryOnCacheIdentity:
    kwargs = {
        "user_id": SAMPLE_USER_ID,
        "canonical_product_id": SAMPLE_PRODUCT_ID,
        "shopper_image_sha256": SAMPLE_HASH_1,
        "garment_image_sha256": SAMPLE_HASH_2,
        "shopper_asset_version": 1,
        "garment_image_version": 1,
        "provider": "fashn",
        "provider_model": "tryon-v1.6",
        "provider_model_version": "2026.1",
        "config_version": "v1.0",
        "preprocessing_version": "prep-v1",
        "policy_version": "policy-2026",
        "garment_category": "tops",
        "output_options": {"quality": "high", "nsfw_filter": True},
    }
    kwargs.update(overrides)
    return TryOnCacheIdentity(**kwargs)


def test_identical_parameters_produce_identical_key():
    """CACHE-001: Identical inputs produce the exact same SHA-256 key."""
    id1 = create_base_identity()
    id2 = create_base_identity()
    assert compute_cache_key(id1) == compute_cache_key(id2)


def test_different_user_produces_different_key():
    """CACHE-002: Different user_id produces completely different cache key (isolation)."""
    id1 = create_base_identity(user_id=SAMPLE_USER_ID)
    id2 = create_base_identity(user_id=OTHER_USER_ID)
    assert compute_cache_key(id1) != compute_cache_key(id2)


def test_different_product_produces_different_key():
    """CACHE-003: Different canonical_product_id produces different key."""
    id1 = create_base_identity(canonical_product_id=SAMPLE_PRODUCT_ID)
    id2 = create_base_identity(canonical_product_id=OTHER_PRODUCT_ID)
    assert compute_cache_key(id1) != compute_cache_key(id2)


def test_different_shopper_image_hash_produces_different_key():
    """CACHE-004: Different shopper_image_sha256 produces different key."""
    id1 = create_base_identity(shopper_image_sha256=SAMPLE_HASH_1)
    id2 = create_base_identity(shopper_image_sha256=SAMPLE_HASH_3)
    assert compute_cache_key(id1) != compute_cache_key(id2)


def test_different_garment_image_hash_produces_different_key():
    """CACHE-005: Different garment_image_sha256 produces different key."""
    id1 = create_base_identity(garment_image_sha256=SAMPLE_HASH_2)
    id2 = create_base_identity(garment_image_sha256=SAMPLE_HASH_3)
    assert compute_cache_key(id1) != compute_cache_key(id2)


def test_different_shopper_version_produces_different_key():
    """CACHE-006: Different shopper_asset_version produces different key."""
    id1 = create_base_identity(shopper_asset_version=1)
    id2 = create_base_identity(shopper_asset_version=2)
    assert compute_cache_key(id1) != compute_cache_key(id2)


def test_different_garment_version_produces_different_key():
    """CACHE-007: Different garment_image_version produces different key."""
    id1 = create_base_identity(garment_image_version=1)
    id2 = create_base_identity(garment_image_version=2)
    assert compute_cache_key(id1) != compute_cache_key(id2)


def test_different_provider_produces_different_key():
    """CACHE-008: Different provider produces different key."""
    id1 = create_base_identity(provider="fashn")
    id2 = create_base_identity(provider="mock")
    assert compute_cache_key(id1) != compute_cache_key(id2)


def test_different_model_produces_different_key():
    """CACHE-009: Different provider_model produces different key."""
    id1 = create_base_identity(provider_model="tryon-v1.6")
    id2 = create_base_identity(provider_model="tryon-v2.0")
    assert compute_cache_key(id1) != compute_cache_key(id2)


def test_different_model_version_produces_different_key():
    """CACHE-010: Different provider_model_version produces different key."""
    id1 = create_base_identity(provider_model_version="2026.1")
    id2 = create_base_identity(provider_model_version="2026.2")
    assert compute_cache_key(id1) != compute_cache_key(id2)


def test_different_config_version_produces_different_key():
    """CACHE-011: Different config_version produces different key."""
    id1 = create_base_identity(config_version="v1.0")
    id2 = create_base_identity(config_version="v1.1")
    assert compute_cache_key(id1) != compute_cache_key(id2)


def test_different_preprocessing_version_produces_different_key():
    """CACHE-012: Different preprocessing_version produces different key."""
    id1 = create_base_identity(preprocessing_version="prep-v1")
    id2 = create_base_identity(preprocessing_version="prep-v2")
    assert compute_cache_key(id1) != compute_cache_key(id2)


def test_different_policy_version_produces_different_key():
    """CACHE-013: Different policy_version produces different key."""
    id1 = create_base_identity(policy_version="policy-2026")
    id2 = create_base_identity(policy_version="policy-2027")
    assert compute_cache_key(id1) != compute_cache_key(id2)


def test_different_garment_category_produces_different_key():
    """CACHE-014: Different garment_category produces different key."""
    id1 = create_base_identity(garment_category="tops")
    id2 = create_base_identity(garment_category="bottoms")
    assert compute_cache_key(id1) != compute_cache_key(id2)


def test_output_options_ordering_does_not_affect_key():
    """CACHE-015: Key order in output_options dictionary does not alter hash."""
    id1 = create_base_identity(output_options={"a": 1, "b": 2, "c": 3})
    id2 = create_base_identity(output_options={"c": 3, "a": 1, "b": 2})
    assert compute_cache_key(id1) == compute_cache_key(id2)


def test_different_output_options_produce_different_key():
    """CACHE-016: Changing output options changes the key."""
    id1 = create_base_identity(output_options={"mode": "performance"})
    id2 = create_base_identity(output_options={"mode": "quality"})
    assert compute_cache_key(id1) != compute_cache_key(id2)


def test_invalid_shopper_hash_raises_value_error():
    """CACHE-017: Non-hex or invalid length shopper hash raises ValueError."""
    id_bad = create_base_identity(shopper_image_sha256="not-a-valid-sha256")
    with pytest.raises(ValueError, match="Invalid shopper_image_sha256"):
        compute_cache_key(id_bad)


def test_invalid_garment_hash_raises_value_error():
    """CACHE-018: Non-hex or invalid length garment hash raises ValueError."""
    id_bad = create_base_identity(garment_image_sha256="short_hash")
    with pytest.raises(ValueError, match="Invalid garment_image_sha256"):
        compute_cache_key(id_bad)


def test_negative_version_raises_value_error():
    """CACHE-019: Negative or zero asset version raises ValueError."""
    id_bad = create_base_identity(shopper_asset_version=0)
    with pytest.raises(ValueError, match="Invalid shopper_asset_version"):
        compute_cache_key(id_bad)


def test_empty_required_field_raises_value_error():
    """CACHE-020: Empty string in required identity field raises ValueError."""
    id_bad = create_base_identity(provider="")
    with pytest.raises(ValueError, match="provider must not be empty"):
        compute_cache_key(id_bad)
