"""Explicit shopper feedback scoring (Task 8.4.9)."""

from __future__ import annotations

from collections.abc import Sequence

from fashx.ranking.enums import FeedbackType

FEEDBACK_WEIGHTS: dict[str, float] = {
    FeedbackType.LIKE.value: 1.0,
    FeedbackType.SAVE.value: 0.5,
    FeedbackType.REMOVE_SAVED.value: -0.2,
    FeedbackType.DISLIKE.value: -1.0,
    FeedbackType.NOT_INTERESTED.value: -1.0,
}


def explicit_feedback_score(events: Sequence[str]) -> float:
    """Compute normalized [0.0, 1.0] feedback score from explicit feedback events.

    Passive interactions (e.g. ``VIEW``) are ignored. When conflicting explicit
    feedback events exist, the latest valid state takes precedence when an
    explicit negative rejection is present, or averages active signals.
    """
    if not events:
        return 0.5
    values = [FEEDBACK_WEIGHTS[e] for e in events if e in FEEDBACK_WEIGHTS]
    if not values:
        return 0.5

    # Latest valid explicit event precedence for direct conflicts
    if any(v > 0 for v in values) and any(v < 0 for v in values):
        latest = values[-1]
        return max(0.0, min(1.0, 0.5 + latest / 2))

    average = sum(values) / len(values)
    return max(0.0, min(1.0, 0.5 + average / 2))
