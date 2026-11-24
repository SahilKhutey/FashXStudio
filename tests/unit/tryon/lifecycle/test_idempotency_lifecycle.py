"""Unit tests for request hashing and idempotency conflict detection (Phase 07.4)."""

from __future__ import annotations

from uuid import uuid4

from fashx.tryon.idempotency import compute_request_hash


def test_same_request_produces_identical_hash() -> None:
    u = uuid4()
    p = uuid4()
    o = uuid4()
    s = uuid4()
    g = uuid4()

    args = {
        "user_id": u,
        "product_id": p,
        "offer_id": o,
        "shopper_asset_id": s,
        "garment_asset_id": g,
        "shopper_asset_version": 1,
        "garment_asset_version": 2,
        "provider": "fashn_api",
        "model_version": "tryon-v1.6",
        "validation_policy_version": "v1.0",
    }
    hash1 = compute_request_hash(**args)
    hash2 = compute_request_hash(**args)

    assert hash1 == hash2
    assert len(hash1) == 64


def test_changed_asset_version_changes_hash() -> None:
    u = uuid4()
    p = uuid4()
    s = uuid4()

    base = {
        "user_id": u,
        "product_id": p,
        "shopper_asset_id": s,
        "shopper_asset_version": 1,
    }
    hash_v1 = compute_request_hash(**base)
    hash_v2 = compute_request_hash(**{**base, "shopper_asset_version": 2})

    assert hash_v1 != hash_v2


def test_changed_product_changes_hash() -> None:
    u = uuid4()
    s = uuid4()

    h1 = compute_request_hash(user_id=u, product_id=uuid4(), shopper_asset_id=s)
    h2 = compute_request_hash(user_id=u, product_id=uuid4(), shopper_asset_id=s)

    assert h1 != h2


def test_changed_validation_policy_changes_hash() -> None:
    u = uuid4()
    p = uuid4()
    s = uuid4()

    h1 = compute_request_hash(user_id=u, product_id=p, shopper_asset_id=s, validation_policy_version="v1.0")
    h2 = compute_request_hash(user_id=u, product_id=p, shopper_asset_id=s, validation_policy_version="v2.0")

    assert h1 != h2
