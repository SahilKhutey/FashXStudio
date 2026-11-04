from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from fashx.discovery.taste_vector import (
    TasteSignal,
    build_taste_vector,
    compute_time_decay,
)


def make_vector(seed_val: float, dim: int = 512) -> list[float]:
    vec = [seed_val * (0.01 * (i % 10 + 1)) for i in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def test_taste_vector_cold_start_empty() -> None:
    res = build_taste_vector(
        signals=[],
        target_model_id="Marqo/marqo-fashionCLIP",
        target_model_version="2026.1",
    )
    assert res is None


def test_taste_vector_model_compatibility_filter() -> None:
    now = datetime.now(UTC)
    v1 = make_vector(1.0)
    # Signal from older model version
    old_signal = TasteSignal(
        garment_id="g1",
        action="like",
        timestamp=now,
        embedding=v1,
        model_id="Marqo/marqo-fashionCLIP",
        model_version="2025.1",
    )
    # Target is 2026.1 -> incompatible
    res = build_taste_vector(
        signals=[old_signal],
        target_model_id="Marqo/marqo-fashionCLIP",
        target_model_version="2026.1",
    )
    assert res is None


def test_taste_vector_single_signal_normalized() -> None:
    now = datetime.now(UTC)
    v1 = make_vector(1.0)
    signal = TasteSignal(
        garment_id="g1",
        action="like",
        timestamp=now,
        embedding=v1,
        model_id="Marqo/marqo-fashionCLIP",
        model_version="2026.1",
    )
    res = build_taste_vector(
        signals=[signal],
        target_model_id="Marqo/marqo-fashionCLIP",
        target_model_version="2026.1",
        now=now,
    )
    assert res is not None
    assert len(res) == 512
    norm = math.sqrt(sum(x * x for x in res))
    assert abs(norm - 1.0) < 1e-4
    # Direction matches v1
    for a, b in zip(res, v1, strict=False):
        assert abs(a - b) < 1e-4


def test_taste_vector_time_decay() -> None:
    now = datetime.now(UTC)
    t_14_days_ago = now - timedelta(days=14)
    decay_14 = compute_time_decay(t_14_days_ago, now=now, half_life_days=14.0)
    assert abs(decay_14 - 0.5) < 1e-3

    t_28_days_ago = now - timedelta(days=28)
    decay_28 = compute_time_decay(t_28_days_ago, now=now, half_life_days=14.0)
    assert abs(decay_28 - 0.25) < 1e-3


def test_taste_vector_negative_and_positive_interaction() -> None:
    now = datetime.now(UTC)
    v1 = make_vector(1.0)
    v2 = make_vector(2.0)

    # Only negative signals -> returns None
    neg_signal = TasteSignal(
        garment_id="g1",
        action="hide",
        timestamp=now,
        embedding=v1,
        model_id="Marqo/marqo-fashionCLIP",
        model_version="2026.1",
    )
    assert (
        build_taste_vector(
            signals=[neg_signal],
            target_model_id="Marqo/marqo-fashionCLIP",
            target_model_version="2026.1",
        )
        is None
    )

    # Mix positive and negative
    pos_signal = TasteSignal(
        garment_id="g2",
        action="save",
        timestamp=now,
        embedding=v2,
        model_id="Marqo/marqo-fashionCLIP",
        model_version="2026.1",
    )
    res = build_taste_vector(
        signals=[neg_signal, pos_signal],
        target_model_id="Marqo/marqo-fashionCLIP",
        target_model_version="2026.1",
        now=now,
    )
    assert res is not None
    assert len(res) == 512
    norm = math.sqrt(sum(x * x for x in res))
    assert abs(norm - 1.0) < 1e-4
