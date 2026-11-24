"""Deterministic cache identity and key computation for Virtual Try-On results.

Architecture & Security Invariants:
1. Every cache key MUST include the requesting user_id. Private try-on results
   must NEVER be shared across different shoppers, regardless of garment identity.
2. Canonical sorting and deterministic JSON serialization ensure stable hashing.
3. Any alteration in image contents (SHA-256), versions, models, or policies
   produces a distinct hash, preventing stale or misapplied inference outputs.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

SHA256_HEX_REGEX = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)


@dataclass(frozen=True)
class TryOnCacheIdentity:
    """Canonical identity parameters required to identify or reuse a VTO result."""

    user_id: UUID
    canonical_product_id: UUID
    shopper_image_sha256: str
    garment_image_sha256: str
    shopper_asset_version: int
    garment_image_version: int
    provider: str
    provider_model: str
    provider_model_version: str
    config_version: str
    preprocessing_version: str
    policy_version: str
    garment_category: str
    output_options: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate integrity and format of cache identity fields."""
        if not self.user_id:
            raise ValueError("user_id is required for cache isolation")
        if not self.canonical_product_id:
            raise ValueError("canonical_product_id is required")

        shopper_hash = self.shopper_image_sha256.lower().strip()
        if not SHA256_HEX_REGEX.match(shopper_hash):
            raise ValueError(f"Invalid shopper_image_sha256: {self.shopper_image_sha256}")

        garment_hash = self.garment_image_sha256.lower().strip()
        if not SHA256_HEX_REGEX.match(garment_hash):
            raise ValueError(f"Invalid garment_image_sha256: {self.garment_image_sha256}")

        if self.shopper_asset_version < 1:
            raise ValueError(f"Invalid shopper_asset_version: {self.shopper_asset_version}")
        if self.garment_image_version < 1:
            raise ValueError(f"Invalid garment_image_version: {self.garment_image_version}")

        for field_name, val in [
            ("provider", self.provider),
            ("provider_model", self.provider_model),
            ("provider_model_version", self.provider_model_version),
            ("config_version", self.config_version),
            ("preprocessing_version", self.preprocessing_version),
            ("policy_version", self.policy_version),
            ("garment_category", self.garment_category),
        ]:
            if not val or not val.strip():
                raise ValueError(f"{field_name} must not be empty")


def compute_output_options_hash(output_options: dict[str, Any] | None) -> str:
    """Compute deterministic SHA-256 hash of output options dictionary."""
    if not output_options:
        normalized_str = "{}"
    else:
        normalized_str = json.dumps(
            output_options,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            default=str,
        )
    return hashlib.sha256(normalized_str.encode("utf-8")).hexdigest()


def compute_cache_key(identity: TryOnCacheIdentity) -> str:
    """Compute canonical composite SHA-256 cache key for VTO result lookup.

    Formula:
        SHA256(
            user_id:canonical_product_id:shopper_image_sha256:garment_image_sha256:
            shopper_asset_version:garment_image_version:provider:provider_model:
            provider_model_version:config_version:preprocessing_version:
            policy_version:garment_category:output_options_hash
        )
    """
    identity.validate()

    options_hash = compute_output_options_hash(identity.output_options)

    canonical_payload = (
        f"{identity.user_id}:"
        f"{identity.canonical_product_id}:"
        f"{identity.shopper_image_sha256.lower()}:"
        f"{identity.garment_image_sha256.lower()}:"
        f"{identity.shopper_asset_version}:"
        f"{identity.garment_image_version}:"
        f"{identity.provider.lower().strip()}:"
        f"{identity.provider_model.lower().strip()}:"
        f"{identity.provider_model_version.strip()}:"
        f"{identity.config_version.strip()}:"
        f"{identity.preprocessing_version.strip()}:"
        f"{identity.policy_version.strip()}:"
        f"{identity.garment_category.lower().strip()}:"
        f"{options_hash}"
    )

    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
