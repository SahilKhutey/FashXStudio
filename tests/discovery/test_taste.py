"""Tests for taste vector decay and cold start archetype blending (Step 7.13)."""

from datetime import UTC, datetime, timedelta

import numpy as np

from eval.persona_to_context import style_to_embedding
from fashx.discovery.taste import (
    HALF_LIFE_DAYS,
    SignalEvent,
    compute_archetype_vector,
    compute_taste_vector,
    signal_decay_factor,
)


def test_signal_decay_half_life() -> None:
    now = datetime(2026, 10, 10, 12, 0, tzinfo=UTC)
    t0 = now - timedelta(days=HALF_LIFE_DAYS)
    factor = signal_decay_factor(t0, now)
    assert abs(factor - 0.5) < 1e-4

    t_double = now - timedelta(days=HALF_LIFE_DAYS * 2)
    factor_double = signal_decay_factor(t_double, now)
    assert abs(factor_double - 0.25) < 1e-4


def test_cold_start_archetype_when_zero_signals() -> None:
    vec = compute_taste_vector([], user_styles=["minimal", "casual"])
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-5

    # Should match archetype vector directly
    archetype = compute_archetype_vector(["minimal", "casual"])
    assert np.allclose(vec, archetype, atol=1e-5)


def test_blend_archetype_with_few_signals() -> None:
    now = datetime(2026, 10, 10, 12, 0, tzinfo=UTC)
    garment_emb = style_to_embedding("ethnic")

    # 1 signal (<3)
    ev = SignalEvent(garment_id="g1", action="like", timestamp=now, embedding=garment_emb)
    vec = compute_taste_vector([ev], user_styles=["minimal"], now=now)

    assert abs(np.linalg.norm(vec) - 1.0) < 1e-5
    # Since it's a 70/30 blend, dot product with ethnic garment should be positive and between archetype & garment
    assert float(np.dot(vec, garment_emb)) > 0.0


def test_full_signals_when_three_or_more() -> None:
    now = datetime(2026, 10, 10, 12, 0, tzinfo=UTC)
    e1 = style_to_embedding("streetwear")
    e2 = style_to_embedding("streetwear")
    e3 = style_to_embedding("streetwear")

    events = [
        SignalEvent(garment_id="g1", action="like", timestamp=now, embedding=e1),
        SignalEvent(garment_id="g2", action="try_on", timestamp=now, embedding=e2),
        SignalEvent(garment_id="g3", action="like", timestamp=now, embedding=e3),
    ]

    vec = compute_taste_vector(events, user_styles=["formal"], now=now)
    assert abs(np.linalg.norm(vec) - 1.0) < 1e-5
    # >=3 signals ignore cold-start archetype and align fully with observed signals
    assert float(np.dot(vec, e1)) > 0.95
