"""Feedback bias, cold-start, and pipeline monitoring metrics (Task 8.5.13)."""

from __future__ import annotations

from dataclasses import dataclass

from fashx.feedback.enums import FeedbackEventType, ReactionState
from fashx.feedback.repository import InMemoryFeedbackRepository


@dataclass(frozen=True)
class FeedbackMonitoringSnapshot:
    events_received: int
    events_processed: int
    events_skipped: int
    events_dead_lettered: int
    likes_count: int
    dislikes_count: int
    saved_active_count: int
    impressions_count: int
    clicks_count: int
    ctr: float
    outbound_clicks_count: int
    active_personalization_shoppers: int


def compute_feedback_monitoring(
    repository: InMemoryFeedbackRepository,
) -> FeedbackMonitoringSnapshot:
    """Compute operational and bias-monitoring metrics from the feedback store."""
    events = list(repository.events.values())
    processed = sum(1 for e in events if e.processing_status == "PROCESSED")
    skipped = sum(1 for e in events if e.processing_status == "SKIPPED")
    dead = sum(1 for e in events if e.processing_status == "DEAD_LETTERED")

    likes = sum(1 for r in repository.reactions.values() if r.reaction == ReactionState.LIKE)
    dislikes = sum(1 for r in repository.reactions.values() if r.reaction == ReactionState.DISLIKE)
    saved = sum(1 for s in repository.saved.values() if s.is_saved)

    impressions = sum(
        1 for e in events if e.event_type == FeedbackEventType.PRODUCT_IMPRESSION.value
    )
    clicks = sum(1 for e in events if e.event_type == FeedbackEventType.PRODUCT_CLICKED.value)
    outbound = sum(
        1 for e in events if e.event_type == FeedbackEventType.MERCHANT_OUTBOUND_CLICKED.value
    )
    ctr = round(clicks / impressions, 4) if impressions > 0 else 0.0

    active_shoppers = {r.shopper_id for r in repository.reactions.values()} | {
        s.shopper_id for s in repository.saved.values() if s.is_saved
    }

    return FeedbackMonitoringSnapshot(
        events_received=len(events),
        events_processed=processed,
        events_skipped=skipped,
        events_dead_lettered=dead,
        likes_count=likes,
        dislikes_count=dislikes,
        saved_active_count=saved,
        impressions_count=impressions,
        clicks_count=clicks,
        ctr=ctr,
        outbound_clicks_count=outbound,
        active_personalization_shoppers=len(active_shoppers),
    )
