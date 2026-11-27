"""Merchant-specific variant size availability checks (Task 8.4.7)."""

from __future__ import annotations

from collections.abc import Sequence

from fashx.ranking.contracts import CandidateVariant
from fashx.ranking.enums import AvailabilityStatus, SizeAvailability


def check_size_availability(
    selected_size: str | None,
    variants: Sequence[CandidateVariant],
    *,
    required_size_system: str | None = None,
) -> SizeAvailability:
    """Resolve availability strictly within the merchant's own variants.

    Never cross-matches size labels across distinct merchant sizing systems when
    ``required_size_system`` is specified.
    """
    if selected_size is None or not selected_size.strip():
        return SizeAvailability.NOT_APPLICABLE

    norm_size = selected_size.strip()
    matching = [
        v
        for v in variants
        if v.is_active
        and v.size_label.strip() == norm_size
        and (
            required_size_system is None
            or v.merchant_size_system is None
            or v.merchant_size_system == required_size_system
        )
    ]
    if not matching:
        return SizeAvailability.UNKNOWN
    if any(v.stock_status == AvailabilityStatus.IN_STOCK.value for v in matching):
        return SizeAvailability.AVAILABLE
    if all(v.stock_status == AvailabilityStatus.OUT_OF_STOCK.value for v in matching):
        return SizeAvailability.UNAVAILABLE
    return SizeAvailability.UNKNOWN
