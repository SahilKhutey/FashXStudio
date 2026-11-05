from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

SIGNAL_WEIGHTS: dict[str, float] = {
    "like": 1.0,
    "save": 1.2,
    "try_on": 1.5,
    "hide": -1.0,
    "not_interested": -1.0,
}

HALF_LIFE_DAYS: float = 14.0


@dataclass(frozen=True)
class TasteSignal:
    """Individual user behavioral signal with model provenance."""

    garment_id: str
    action: str
    timestamp: datetime
    embedding: list[float]
    model_id: str
    model_version: str


def compute_time_decay(
    event_time: datetime,
    now: datetime | None = None,
    half_life_days: float = HALF_LIFE_DAYS,
) -> float:
    """Calculate exponential decay factor for an interaction event with 14-day half-life."""
    if now is None:
        now = datetime.now(UTC)

    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    delta_seconds = max(0.0, (now - event_time).total_seconds())
    delta_days = delta_seconds / 86400.0
    return float(0.5 ** (delta_days / half_life_days))


def build_taste_vector(
    signals: Sequence[TasteSignal],
    target_model_id: str,
    target_model_version: str,
    now: datetime | None = None,
    expected_dim: int = 512,
) -> list[float] | None:
    """Compute personalized taste vector strictly from compatible model embeddings with time decay.

    Rules:
    1. Model compatibility: Discard signals from different model_id or model_version.
    2. Missing / cold-start: Return None when no compatible signals exist.
       Caller falls back to pure deterministic preference compatibility without synthetic vectors.
    3. Normalization: Resulting vector is unit-normalized (L2 norm = 1.0).
    4. Negative signals (hide, not_interested) push vector away from those representations.
    """
    if not signals:
        return None

    # Filter to compatible signals only
    compatible_signals = [
        s
        for s in signals
        if s.model_id == target_model_id
        and s.model_version == target_model_version
        and len(s.embedding) == expected_dim
        and all(math.isfinite(x) for x in s.embedding)
    ]

    if not compatible_signals:
        return None

    # Check if there are any positive signals; if only negative signals exist, return None
    has_positive = any(
        SIGNAL_WEIGHTS.get(s.action, 0.0) > 0 for s in compatible_signals
    )
    if not has_positive:
        return None

    accum = [0.0] * expected_dim

    for s in compatible_signals:
        weight = SIGNAL_WEIGHTS.get(s.action, 0.0)
        decay = compute_time_decay(s.timestamp, now=now)
        effective_weight = weight * decay

        for i, val in enumerate(s.embedding):
            accum[i] += effective_weight * val

    norm = math.sqrt(sum(x * x for x in accum))
    if norm < 1e-7 or not math.isfinite(norm):
        return None

    return [float(x / norm) for x in accum]
