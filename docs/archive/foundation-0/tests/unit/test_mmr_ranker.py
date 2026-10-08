from uuid import uuid4

from api.app.recommendation.compatibility import CompatibilityScore
from api.app.recommendation.filters import CandidateItem
from api.app.recommendation.ranker import PersonalizedRanker, ScoredItem


def make_scored(
    category: str,
    color: str,
    cut: str,
    relevance: float,
) -> ScoredItem:
    item = CandidateItem(
        garment_id=uuid4(),
        category=category,
        subcategory="test",
        price_minor=100000,
        in_stock=True,
        dominant_color=color,
        silhouette=cut,
    )
    compat = CompatibilityScore(
        total_score=relevance,
        color_score=0.9,
        silhouette_score=0.9,
        color_reason="good",
        silhouette_reason="good",
    )
    return ScoredItem(item=item, compatibility=compat, relevance_score=relevance)


def test_mmr_diversifies_identical_items() -> None:
    # 3 navy tops of same cut, 1 olive outerwear with slightly lower relevance
    item_navy1 = make_scored("tops", "navy", "slim", 0.95)
    item_navy2 = make_scored("tops", "navy", "slim", 0.94)
    item_navy3 = make_scored("tops", "navy", "slim", 0.93)
    item_outer = make_scored("outerwear", "olive", "relaxed", 0.90)

    candidates = [item_navy1, item_navy2, item_navy3, item_outer]
    ranked = PersonalizedRanker.rank_and_diversify(candidates, top_k=2, diversity_lambda=0.5)

    assert len(ranked) == 2
    # First item must be highest relevance
    assert ranked[0].item.garment_id == item_navy1.item.garment_id
    # Second item should be the diverse outerwear rather than the almost-identical second navy top!
    assert ranked[1].item.garment_id == item_outer.item.garment_id
