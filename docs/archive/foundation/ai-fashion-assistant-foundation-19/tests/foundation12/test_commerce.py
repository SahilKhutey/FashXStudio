from datetime import datetime, timezone
from uuid import UUID, uuid4

from api.app.commerce.integrations.configured_affiliate import ConfiguredAffiliateProvider
from api.app.commerce.ports.affiliate import AffiliateRedirect
from api.app.core.settings import Settings
from schemas.commerce.buy_click import BuyClickCreate
from schemas.events.commerce import BuyClicked


def test_affiliate_provider_preserves_merchant_query_and_adds_tracking() -> None:
    settings = Settings(affiliate_network="mvp", affiliate_tracking_param="afa_click_id", affiliate_source_param="afa_source")
    provider = ConfiguredAffiliateProvider(settings)
    result = provider.build_redirect(
        merchant_url="https://merchant.example/item/42?color=black",
        merchant_id=uuid4(),
        offer_id=uuid4(),
        tracking_id="abc-123",
    )
    assert "color=black" in result.redirect_url
    assert "afa_click_id=abc-123" in result.redirect_url
    assert "afa_source=mvp" in result.redirect_url
    assert result.affiliate_network == "mvp"


def test_affiliate_provider_rejects_invalid_destination() -> None:
    settings = Settings()
    provider = ConfiguredAffiliateProvider(settings)
    try:
        provider.build_redirect(
            merchant_url="javascript:alert(1)",
            merchant_id=uuid4(),
            offer_id=uuid4(),
            tracking_id="abc",
        )
    except ValueError as exc:
        assert "invalid" in str(exc).lower()
    else:
        raise AssertionError("unsafe merchant URL must be rejected")


def test_buy_click_contract_requires_garment_and_offer() -> None:
    garment_id = uuid4()
    offer_id = uuid4()
    request = BuyClickCreate(garment_id=garment_id, offer_id=offer_id)
    assert request.garment_id == garment_id
    assert request.offer_id == offer_id


def test_buy_clicked_event_contains_commerce_attribution() -> None:
    event = BuyClicked.create(
        event_id=uuid4(),
        user_id=uuid4(),
        garment_id=uuid4(),
        offer_id=uuid4(),
        tracking_id="click-1",
        affiliate_network="mvp",
        trace_id=uuid4(),
        occurred_at=datetime.now(timezone.utc),
    )
    assert event.event_type == "buy_clicked"
    assert event.payload["tracking_id"] == "click-1"
    assert event.payload["affiliate_network"] == "mvp"
