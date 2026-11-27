"""Style preference matching with confidence and dislike safeguards (Task 8.4.3)."""

from __future__ import annotations

from collections.abc import Mapping


def filter_confident_styles(
    style_confidences: Mapping[str, float],
    min_confidence: float = 0.70,
) -> set[str]:
    """Return normalized style IDs whose confidence meets the verified threshold."""
    return {
        style.strip().upper()
        for style, confidence in style_confidences.items()
        if confidence >= min_confidence and style.strip()
    }


def style_preference_score(
    product_styles: set[str] | Mapping[str, float],
    liked_styles: dict[str, float],
    disliked_styles: dict[str, float],
    *,
    min_confidence: float = 0.70,
) -> float:
    """Compute normalized [0.0, 1.0] style preference score.

    Returns neutral 0.5 when the shopper has no recorded style preferences or
    when the product has no confident style tags.
    """
    if isinstance(product_styles, Mapping):
        confident_styles = filter_confident_styles(product_styles, min_confidence=min_confidence)
    else:
        confident_styles = {s.strip().upper() for s in product_styles if s.strip()}

    norm_liked = {k.strip().upper(): v for k, v in liked_styles.items() if k.strip()}
    norm_disliked = {k.strip().upper(): v for k, v in disliked_styles.items() if k.strip()}

    if not norm_liked and not norm_disliked:
        return 0.5
    if not confident_styles:
        return 0.5

    positive = [strength for style, strength in norm_liked.items() if style in confident_styles]
    negative = [strength for style, strength in norm_disliked.items() if style in confident_styles]
    positive_score = max(positive, default=0.0)
    negative_penalty = max(negative, default=0.0)

    # Explicit negative feedback outweighs weak historical positive signals
    if negative_penalty >= 0.7 and positive_score < 0.5:
        positive_score = 0.0

    return max(0.0, min(1.0, 0.5 + 0.5 * positive_score - 0.5 * negative_penalty))
