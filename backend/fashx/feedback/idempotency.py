"""Idempotency hashing, UTC timestamp validation, and signal decay helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any


class FeedbackConflict(Exception):
    """Raised when an event_id is reused with a mismatched owner or payload."""


def canonical_payload_hash(payload: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash for an event payload."""
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_occurred_at(
    occurred_at: datetime,
    *,
    now: datetime | None = None,
    max_future_skew_seconds: int = 300,
    max_age_days: int = 90,
) -> datetime:
    """Normalize client occurred_at to UTC and reject unreasonable clock skew."""
    ref = now or datetime.now(UTC)
    ts = occurred_at.astimezone(UTC) if occurred_at.tzinfo else occurred_at.replace(tzinfo=UTC)
    if ts > ref + timedelta(seconds=max_future_skew_seconds):
        raise ValueError("occurred_at cannot be significantly in the future")
    if ts < ref - timedelta(days=max_age_days):
        raise ValueError("occurred_at is outside the accepted event age window")
    return ts


def apply_time_decay(
    initial_weight: float,
    *,
    occurred_at: datetime,
    half_life_days: float,
    now: datetime | None = None,
) -> float:
    """Apply exponential half-life decay W(t) = W_0 * 2^(-dt / H)."""
    if half_life_days <= 0:
        raise ValueError("half_life_days must be positive")
    ref = now or datetime.now(UTC)
    ts = occurred_at.astimezone(UTC) if occurred_at.tzinfo else occurred_at.replace(tzinfo=UTC)
    elapsed_days = max(0.0, (ref - ts).total_seconds() / 86400.0)
    return float(initial_weight * (2.0 ** (-elapsed_days / half_life_days)))
