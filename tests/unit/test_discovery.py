import pytest

from fashx.features.discovery.contracts import DiscoveryRequest
from fashx.features.discovery.enums import DiscoveryItemType, DiscoveryStatus, DiscoverySurface
from fashx.features.discovery.models import DiscoveryItem
from fashx.features.discovery.repository import DiscoveryRepository
from fashx.features.discovery.service import DiscoveryService
from fashx.features.discovery.state import DiscoveryState


def item(
    item_id: str, category: str, relevance: float, trend: float, region: str | None = None
) -> DiscoveryItem:
    return DiscoveryItem(
        item_id,
        DiscoveryItemType.PRODUCT,
        item_id,
        category=category,
        relevance_score=relevance,
        trend_score=trend,
        region=region,
    )


def test_discovery_filters_categories_regions_and_ranks_trends() -> None:
    service = DiscoveryService(
        DiscoveryRepository(
            (
                item("a", "shirts", 0.9, 0.2),
                item("b", "shirts", 0.4, 0.9, "IN"),
                item("c", "outfits", 1.0, 0.1),
            )
        )
    )
    assert service.discover(DiscoveryRequest("user", category="shirts")).items[0].item_id == "a"
    assert (
        service.discover(DiscoveryRequest("user", surface=DiscoverySurface.TRENDING, region="IN"))
        .items[0]
        .item_id
        == "b"
    )


def test_discovery_validates_requests_and_exposes_empty_error_states() -> None:
    with pytest.raises(ValueError):
        DiscoveryService(DiscoveryRepository()).discover(DiscoveryRequest("", limit=0))
    state = DiscoveryState()
    state.loading()
    state.success(False)
    assert state.status == DiscoveryStatus.EMPTY
    state.failure("Unavailable")
    assert state.status == DiscoveryStatus.ERROR and state.error == "Unavailable"
