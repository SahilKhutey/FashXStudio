"""Shopper-scoped ranking result cache with revision-based invalidation."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass

from fashx.ranking.contracts import RankedProductsResponse, RankingContext


def build_ranking_cache_key(
    *,
    shopper_id: str,
    shopper_profile_revision: int,
    context: RankingContext,
    ranking_version: str,
    config_version: str,
    taxonomy_version: str,
    catalog_revision: str = "v1",
    availability_revision: str = "v1",
    visual_reference_hash: str = "none",
) -> str:
    """Build a canonical shopper-scoped SHA-256 cache key."""
    query_payload = json.dumps(
        {
            "query": (context.query or "").strip().lower(),
            "category_id": context.category_id,
            "min_price": str(context.min_price) if context.min_price is not None else None,
            "max_price": str(context.max_price) if context.max_price is not None else None,
            "currency": context.currency.upper(),
            "require_selected_size": context.require_selected_size,
            "page": context.page,
            "page_size": context.page_size,
        },
        sort_keys=True,
    )
    query_hash = hashlib.sha256(query_payload.encode("utf-8")).hexdigest()[:16]
    raw = ":".join(
        [
            "ranking",
            shopper_id,
            str(shopper_profile_revision),
            query_hash,
            context.selected_size or "none",
            ranking_version,
            config_version,
            taxonomy_version,
            catalog_revision,
            availability_revision,
            visual_reference_hash,
        ]
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"ranking:{shopper_id}:{digest}"


@dataclass
class _CacheEntry:
    response: RankedProductsResponse
    expires_at: float
    shopper_id: str


class RankingCache:
    """In-memory shopper-isolated ranking cache with explicit invalidation."""

    def __init__(self) -> None:
        self._entries: dict[str, _CacheEntry] = {}

    def get(self, key: str, *, shopper_id: str) -> RankedProductsResponse | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.shopper_id != shopper_id:
            return None
        if time.monotonic() >= entry.expires_at:
            self._entries.pop(key, None)
            return None
        return entry.response

    def set(
        self,
        key: str,
        response: RankedProductsResponse,
        *,
        shopper_id: str,
        ttl_seconds: int,
    ) -> None:
        self._entries[key] = _CacheEntry(
            response=response,
            expires_at=time.monotonic() + max(1, ttl_seconds),
            shopper_id=shopper_id,
        )

    def invalidate_shopper(self, shopper_id: str) -> None:
        stale_keys = [k for k, v in self._entries.items() if v.shopper_id == shopper_id]
        for k in stale_keys:
            self._entries.pop(k, None)

    def invalidate_all(self) -> None:
        self._entries.clear()
