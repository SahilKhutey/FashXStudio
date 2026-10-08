from .models import DiscoveryItem


def ranking_score(item: DiscoveryItem) -> float:
    return 0.5 * item.relevance_score + 0.3 * item.trend_score + 0.2 * item.popularity_score


def rank_items(items: list[DiscoveryItem]) -> list[DiscoveryItem]:
    return sorted(items, key=ranking_score, reverse=True)
