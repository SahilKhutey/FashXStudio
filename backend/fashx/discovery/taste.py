"""Taste vector computation with exponential signal decay and cold-start archetype blending (Step 7.13)."""

from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np

from eval.persona_to_context import ARCHETYPE_CENTROIDS, style_to_embedding

SIGNAL_WEIGHTS = {
    "like": 1.0,
    "try_on": 2.0,
    "hide": -1.5,
    "not_interested": -1.5,
}

HALF_LIFE_DAYS = 14.0


@dataclass
class SignalEvent:
    garment_id: str
    action: str
    timestamp: datetime
    embedding: np.ndarray


def signal_decay_factor(event_time: datetime, now: datetime | None = None) -> float:
    """Calculate exponential decay factor for an event given 14-day half-life."""
    if now is None:
        now = datetime.now(UTC)

    # Normalize tzinfo
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    delta_days = max(0.0, (now - event_time).total_seconds() / 86400.0)
    return float(0.5 ** (delta_days / HALF_LIFE_DAYS))


def compute_archetype_vector(styles: list[str] | None = None) -> np.ndarray:
    """Compute normalized archetype centroid vector from styles or all archetypes."""
    if styles:
        vecs = [style_to_embedding(s) for s in styles]
        combined = np.mean(vecs, axis=0)
    else:
        combined = np.mean(ARCHETYPE_CENTROIDS, axis=0)

    norm = np.linalg.norm(combined)
    return (combined / norm).astype(np.float32) if norm > 0 else combined.astype(np.float32)


def compute_taste_vector(
    signals: list[SignalEvent],
    user_styles: list[str] | None = None,
    now: datetime | None = None,
) -> np.ndarray:
    """Compute personal taste vector from signals and cold-start preferences.

    - 0 signals: 100% archetype blend with selected style vectors.
    - 1-2 signals (<3): 70% archetype + 30% observed signals vector.
    - >=3 signals: 100% observed signals vector.
    - Unit length normalized (norm=1).
    """
    archetype_vec = compute_archetype_vector(user_styles)

    if not signals:
        return archetype_vec

    # Calculate observed signals vector with decay
    signal_vec = np.zeros(512, dtype=np.float32)
    valid_signals = 0

    for ev in signals:
        weight = SIGNAL_WEIGHTS.get(ev.action, 0.0)
        decay = signal_decay_factor(ev.timestamp, now)
        signal_vec += (weight * decay) * ev.embedding
        valid_signals += 1

    s_norm = np.linalg.norm(signal_vec)
    if s_norm > 0:
        signal_vec = signal_vec / s_norm
    else:
        signal_vec = archetype_vec

    if valid_signals < 3:
        # Blend: 70% archetype + 30% observed signals
        blended = 0.7 * archetype_vec + 0.3 * signal_vec
    else:
        # Full observed signals
        blended = signal_vec

    final_norm = np.linalg.norm(blended)
    if final_norm > 0:
        blended = blended / final_norm

    return blended.astype(np.float32)
