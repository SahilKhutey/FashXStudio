"""Phase 08.4 ranking adapter consuming consented Phase 08.5 projections (Task 8.5.12)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from fashx.feedback.consent import FeedbackConsentService
from fashx.feedback.enums import ReactionState
from fashx.feedback.repository import InMemoryFeedbackRepository


@dataclass(frozen=True)
class ProductPreference:
    """Compact preference projection for a single shopper-product pair."""

    reaction: str
    is_saved: bool
    click_count_30d: int
    detail_view_count_30d: int
    last_explicit_feedback_at: datetime | None
    last_interaction_at: datetime | None


def build_product_feedback_feature(preference: ProductPreference) -> float:
    """Convert a ProductPreference projection into a normalized [0.0, 1.0] ranking feature.

    Explicit negative reactions strictly outweigh passive clicks and saves.
    """
    if preference.reaction == ReactionState.DISLIKE.value:
        return 0.0
    if preference.reaction == ReactionState.LIKE.value:
        return 1.0
    if preference.is_saved:
        return 0.75
    if preference.detail_view_count_30d > 0:
        return 0.60
    if preference.click_count_30d > 0:
        return 0.55
    return 0.50


def build_shopper_feedback_projection(
    *,
    shopper_id: str,
    repository: InMemoryFeedbackRepository,
    consent_service: FeedbackConsentService,
) -> dict[str, ProductPreference]:
    """Build consented per-product feedback projections for Phase 08.4 ranking."""
    if not consent_service.can_personalize(shopper_id):
        return {}

    product_ids: set[str] = set()
    for uid, pid in repository.reactions:
        if uid == shopper_id:
            product_ids.add(pid)
    for uid, pid in repository.saved:
        if uid == shopper_id:
            product_ids.add(pid)
    for uid, pid in repository.interactions:
        if uid == shopper_id:
            product_ids.add(pid)

    projections: dict[str, ProductPreference] = {}
    for pid in sorted(product_ids):
        react = repository.reactions.get((shopper_id, pid))
        saved = repository.saved.get((shopper_id, pid))
        stats = repository.interactions.get((shopper_id, pid))
        projections[pid] = ProductPreference(
            reaction=react.reaction.value if react else ReactionState.NONE.value,
            is_saved=bool(saved and saved.is_saved),
            click_count_30d=stats.click_count if stats else 0,
            detail_view_count_30d=stats.detail_view_count if stats else 0,
            last_explicit_feedback_at=react.updated_at if react else None,
            last_interaction_at=stats.last_interaction_at if stats else None,
        )
    return projections
