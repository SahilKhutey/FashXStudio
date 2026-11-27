"""Mandatory hard eligibility & safety gate preceding ranking (Task 8.4.11)."""

from __future__ import annotations

from datetime import datetime

from fashx.ranking.availability import is_fresh
from fashx.ranking.contracts import EligibilityResult, RankingCandidate, RankingContext
from fashx.ranking.enums import AvailabilityStatus, SizeAvailability
from fashx.ranking.size import check_size_availability


def evaluate_eligibility(
    candidate: RankingCandidate,
    context: RankingContext,
    *,
    max_age_seconds: int = 86400,
    now: datetime | None = None,
) -> EligibilityResult:
    """Enforce all legal, operational, price, currency, freshness, and size gates."""
    reasons: list[str] = []

    if candidate.product_status != "ACTIVE":
        reasons.append("PRODUCT_NOT_ACTIVE")
    if candidate.offer_status != "ACTIVE":
        reasons.append("OFFER_NOT_ACTIVE")
    if candidate.is_taken_down:
        reasons.append("PRODUCT_TAKEN_DOWN")
    if candidate.is_delisted:
        reasons.append("PRODUCT_DELISTED")
    if candidate.is_discontinued:
        reasons.append("PRODUCT_DISCONTINUED")
    if candidate.permissions.permission_expired:
        reasons.append("SOURCE_PERMISSION_EXPIRED")
    if not candidate.permissions.can_display_product:
        reasons.append("DISPLAY_NOT_AUTHORIZED")
    if not candidate.permissions.can_redirect_to_merchant:
        reasons.append("REDIRECT_NOT_AUTHORIZED")
    if not candidate.permissions.can_display_image:
        reasons.append("IMAGE_DISPLAY_NOT_AUTHORIZED")
    if candidate.availability_status != AvailabilityStatus.IN_STOCK.value:
        reasons.append("OFFER_NOT_CONFIRMED_IN_STOCK")
    if not is_fresh(candidate.availability_verified_at, max_age_seconds, now=now):
        reasons.append("AVAILABILITY_STALE")

    if candidate.price is None or not candidate.currency:
        reasons.append("PRICE_UNAVAILABLE")
    elif candidate.currency.strip().upper() != context.currency.strip().upper():
        reasons.append("CURRENCY_MISMATCH")
    else:
        if context.min_price is not None and candidate.price < context.min_price:
            reasons.append("PRICE_BELOW_MINIMUM")
        if context.max_price is not None and candidate.price > context.max_price:
            reasons.append("PRICE_ABOVE_MAXIMUM")

    size_status = check_size_availability(context.selected_size, candidate.variants)
    require_size = bool(context.selected_size and context.require_selected_size)
    if context.selected_size and size_status == SizeAvailability.UNAVAILABLE:
        reasons.append("SELECTED_SIZE_UNAVAILABLE")
    elif require_size and size_status != SizeAvailability.AVAILABLE:
        reasons.append("SELECTED_SIZE_UNAVAILABLE")

    return EligibilityResult(
        eligible=not reasons,
        size_availability=size_status,
        reason_codes=tuple(reasons),
    )
