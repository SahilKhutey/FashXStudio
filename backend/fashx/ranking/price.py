"""Price preference scoring using Decimal arithmetic (Task 8.4.5)."""

from __future__ import annotations

from decimal import Decimal


def price_preference_score(
    price: Decimal | None,
    minimum: Decimal | None,
    maximum: Decimal | None,
    *,
    offer_currency: str | None = None,
    target_currency: str | None = None,
) -> float:
    """Compute normalized [0.0, 1.0] price preference score using Decimal arithmetic."""
    if price is None:
        return 0.0
    if (
        offer_currency is not None
        and target_currency is not None
        and offer_currency.strip().upper() != target_currency.strip().upper()
    ):
        raise ValueError(
            f"Currency mismatch: offer '{offer_currency}' vs target '{target_currency}'"
        )

    if minimum is None and maximum is None:
        return 0.5
    if minimum is not None and price < minimum:
        return 0.0
    if maximum is not None and price > maximum:
        return 0.0

    if minimum is not None and maximum is not None:
        midpoint = (minimum + maximum) / Decimal("2")
        half_range = (maximum - minimum) / Decimal("2")
        if half_range <= 0:
            return 1.0 if price == minimum else 0.0
        distance = abs(price - midpoint) / half_range
        return float(max(Decimal("0"), Decimal("1") - distance * Decimal("0.25")))

    return 1.0
