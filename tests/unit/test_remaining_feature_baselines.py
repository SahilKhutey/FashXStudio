import pytest

from fashx.features.commerce.models import CartLine
from fashx.features.commerce.service import CommerceService
from fashx.features.engagement.models import Engagement
from fashx.features.engagement.service import EngagementService
from fashx.features.integration.orchestrator import IntegrationOrchestrator
from fashx.features.integration.workflows import WorkflowName
from fashx.features.regional.models import RegionalContext
from fashx.features.regional.service import RegionalService
from fashx.features.shopping.models import ComparableProduct
from fashx.features.shopping.service import ShoppingService


def test_shopping_wishlist_and_comparison() -> None:
    service = ShoppingService()
    service.save("user-1", "product-1")
    assert service.wishlist("user-1") == ("product-1",)
    comparison = service.compare("user-1", (ComparableProduct("a", "A", 100), ComparableProduct("b", "B", 200)))
    assert len(comparison.products) == 2


def test_commerce_order_is_idempotent() -> None:
    service = CommerceService()
    service.add_line("user-1", CartLine("product-1", None, 2, 99))
    first = service.place_order("user-1", "checkout-1")
    assert service.place_order("user-1", "checkout-1") == first
    assert first.total == 198


def test_regional_and_engagement_boundaries() -> None:
    regional = RegionalService()
    assert regional.set_context("user-1", RegionalContext("India", "tropical")).region == "India"
    engagement = EngagementService()
    engagement.record(Engagement("user-1", "product-1", "like"))
    assert len(engagement.events_for("user-1")) == 1
    with pytest.raises(ValueError):
        engagement.record(Engagement("user-1", "product-1", "notify"))


class Adapter:
    def __init__(self, marker: str) -> None:
        self.marker = marker

    def execute(self, action: str, context: dict[str, object]) -> dict[str, str]:
        return {self.marker: action}


def test_integration_degrades_optional_and_stops_required_step() -> None:
    integration = IntegrationOrchestrator({"FX-F02": Adapter("profile"), "FX-F03": Adapter("feed")})
    result = integration.execute(WorkflowName.ONBOARDING_TO_DISCOVERY, {"user_id": "user-1"})
    assert result.completed and len(result.warnings) == 2
    unavailable = integration.execute(WorkflowName.SHOPPING_TO_COMMERCE, {"user_id": "user-1"})
    assert not unavailable.completed
