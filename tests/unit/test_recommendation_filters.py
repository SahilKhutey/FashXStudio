from uuid import uuid4

from fashx.recommendation.filters import (
    CandidateItem,
    DeterministicFilter,
    FilterCriteria,
)


def make_candidate(
    category: str = "tops",
    price_minor: int = 200000,
    in_stock: bool = True,
    dominant_color: str | None = "navy",
) -> CandidateItem:
    return CandidateItem(
        garment_id=uuid4(),
        category=category,
        subcategory="shirts",
        price_minor=price_minor,
        in_stock=in_stock,
        dominant_color=dominant_color,
    )


def test_filter_drops_out_of_stock() -> None:
    item = make_candidate(in_stock=False)
    passed, reason = DeterministicFilter.filter_candidate(item, FilterCriteria())
    assert passed is False
    assert "out of stock" in reason.lower()


def test_filter_enforces_budget_ceiling() -> None:
    item = make_candidate(price_minor=350000)
    criteria = FilterCriteria(budget_max=250000)
    passed, reason = DeterministicFilter.filter_candidate(item, criteria)
    assert passed is False
    assert "budget" in reason.lower()


def test_filter_enforces_avoided_colors() -> None:
    item = make_candidate(dominant_color="yellow")
    criteria = FilterCriteria(avoided_colors=["yellow", "orange"])
    passed, reason = DeterministicFilter.filter_candidate(item, criteria)
    assert passed is False
    assert "avoided" in reason.lower()


def test_filter_enforces_category_restrictions() -> None:
    item = make_candidate(category="shoes")
    criteria = FilterCriteria(allowed_categories=["tops", "bottoms"])
    passed, reason = DeterministicFilter.filter_candidate(item, criteria)
    assert passed is False
    assert "category" in reason.lower()


def test_filter_passes_valid_item() -> None:
    item = make_candidate(category="tops", price_minor=150000, in_stock=True, dominant_color="navy")
    criteria = FilterCriteria(
        budget_max=200000,
        allowed_categories=["tops"],
        avoided_colors=["red"],
    )
    passed, reason = DeterministicFilter.filter_candidate(item, criteria)
    assert passed is True
    assert reason is None
