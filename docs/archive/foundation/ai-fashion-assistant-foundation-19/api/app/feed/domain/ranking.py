from __future__ import annotations


def feed_reasons(*, is_new: bool = True, category_filtered: bool = False, price_filtered: bool = False) -> list[str]:
    reasons: list[str] = ["curated"]
    if is_new:
        reasons.append("new_arrival")
    if category_filtered:
        reasons.append("category_match")
    if price_filtered:
        reasons.append("budget_match")
    return reasons
