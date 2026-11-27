"""Canonical product & offer availability checks (Task 8.4.6)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fashx.ranking.contracts import RankingCandidate
from fashx.ranking.enums import AvailabilityStatus

PURCHASABLE_STATES: frozenset[str] = frozenset({AvailabilityStatus.IN_STOCK.value})


def is_fresh(
    verified_at: datetime | None,
    max_age_seconds: int,
    *,
    now: datetime | None = None,
) -> bool:
    """Return True if availability timestamp is present and within the freshness window."""
    if verified_at is None:
        return True
    ref = now or datetime.now(UTC)
    ts = verified_at if verified_at.tzinfo is not None else verified_at.replace(tzinfo=UTC)
    return (ref - ts) <= timedelta(seconds=max_age_seconds)


def is_purchasable(
    candidate: RankingCandidate,
    *,
    max_age_seconds: int = 86400,
    now: datetime | None = None,
) -> bool:
    """Verify operational and permission eligibility for purchasable ranking."""
    if candidate.product_status != "ACTIVE":
        return False
    if candidate.offer_status != "ACTIVE":
        return False
    if candidate.is_taken_down or candidate.is_delisted or candidate.is_discontinued:
        return False
    if candidate.availability_status not in PURCHASABLE_STATES:
        return False
    if candidate.permissions.permission_expired:
        return False
    if not candidate.permissions.can_display_product:
        return False
    if not candidate.permissions.can_redirect_to_merchant:
        return False
    if not is_fresh(candidate.availability_verified_at, max_age_seconds, now=now):
        return False
    return True


def availability_score(candidate: RankingCandidate, *, max_age_seconds: int = 86400) -> float:
    """Return 1.0 for confirmed fresh IN_STOCK offers, 0.0 otherwise."""
    return 1.0 if is_purchasable(candidate, max_age_seconds=max_age_seconds) else 0.0
