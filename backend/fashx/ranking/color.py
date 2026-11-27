"""Colour preference scoring with primary/secondary & confidence guards (Task 8.4.4)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping


def color_preference_score(
    product_colors: Iterable[str],
    preferred_colors: set[str] | frozenset[str],
    disliked_colors: set[str] | frozenset[str],
    *,
    secondary_colors: Iterable[str] = (),
    color_confidences: Mapping[str, float] | None = None,
    min_confidence: float = 0.70,
) -> float:
    """Compute normalized [0.0, 1.0] colour preference score."""
    norm_pref = {c.strip().upper() for c in preferred_colors if c.strip()}
    norm_disliked = {c.strip().upper() for c in disliked_colors if c.strip()}
    if not norm_pref and not norm_disliked:
        return 0.5

    conf = {k.strip().upper(): v for k, v in (color_confidences or {}).items()}

    def _confident(items: Iterable[str]) -> set[str]:
        out: set[str] = set()
        for raw in items:
            c = raw.strip().upper()
            if not c:
                continue
            if c in conf and conf[c] < min_confidence:
                continue
            out.add(c)
        return out

    primary_set = _confident(product_colors)
    secondary_set = _confident(secondary_colors)
    all_colors = primary_set | secondary_set
    if not all_colors:
        return 0.5

    liked_primary = bool(primary_set & norm_pref)
    liked_secondary = bool(secondary_set & norm_pref)
    disliked = bool(all_colors & norm_disliked)

    if (liked_primary or liked_secondary) and disliked:
        return 0.5
    if disliked:
        return 0.0
    if liked_primary:
        return 1.0
    if liked_secondary:
        return 0.75
    return 0.5
