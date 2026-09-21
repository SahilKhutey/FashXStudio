from .contracts import DiscoveryInteraction, DiscoveryRequest
from .enums import DiscoverySurface
from .models import DiscoveryItem, DiscoveryResult
from .ranking import rank_items
from .repository import DiscoveryRepository


class DiscoveryService:
    def __init__(self, repository: DiscoveryRepository) -> None:
        self.repository = repository

    def discover(self, request: DiscoveryRequest) -> DiscoveryResult:
        if not request.user_id.strip() or not 1 <= request.limit <= 100:
            raise ValueError("A user ID and a limit between 1 and 100 are required.")
        items = list(self.repository.all())
        if request.category:
            items = [item for item in items if item.category == request.category]
        if request.region:
            items = [item for item in items if item.region in {None, request.region}]
        items = (
            sorted(items, key=lambda item: item.trend_score, reverse=True)
            if request.surface == DiscoverySurface.TRENDING
            else rank_items(items)
        )
        selected = tuple(items[: request.limit])
        return DiscoveryResult(items=selected, total=len(selected), surface=request.surface)

    def get_item(self, item_id: str) -> DiscoveryItem | None:
        return self.repository.find(item_id)

    def record_interaction(self, interaction: DiscoveryInteraction) -> None:
        del interaction  # F09 will attach this port to Core analytics.
