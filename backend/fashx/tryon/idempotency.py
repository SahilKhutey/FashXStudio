"""Idempotency and Canonical Request Hashing (Phase 07.4)."""

from __future__ import annotations

import hashlib
import json
from uuid import UUID


def compute_request_hash(
    *,
    user_id: UUID | str,
    product_id: UUID | str,
    offer_id: UUID | str | None = None,
    shopper_asset_id: UUID | str,
    garment_asset_id: UUID | str | None = None,
    shopper_asset_version: int = 1,
    garment_asset_version: int = 1,
    provider: str = "fashn_api",
    model_version: str = "tryon-v1.6",
    validation_policy_version: str = "v1.0",
) -> str:
    """Computes a deterministic canonical SHA-256 hash representing the exact input parameters of a VTO job."""
    canonical = {
        "user_id": str(user_id),
        "product_id": str(product_id),
        "offer_id": str(offer_id) if offer_id else "",
        "shopper_asset_id": str(shopper_asset_id),
        "garment_asset_id": str(garment_asset_id) if garment_asset_id else "",
        "shopper_asset_version": int(shopper_asset_version),
        "garment_asset_version": int(garment_asset_version),
        "provider": str(provider),
        "model_version": str(model_version),
        "validation_policy_version": str(validation_policy_version),
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
