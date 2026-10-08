from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest

from api.app.commerce import application as commerce_module
from api.app.commerce.application import CommerceService
from api.app.commerce.ports.affiliate import AffiliateRedirect
from schemas.commerce.buy_click import BuyClickCreate


class FakeSession:
    pass


class FakeCatalog:
    def __init__(self, offer) -> None:
        self.session = FakeSession()
        self.offer = offer

    async def get_offer(self, garment_id, offer_id):
        return self.offer if self.offer and self.offer.id == offer_id and self.offer.garment_id == garment_id else None


class FakeCommerce:
    def __init__(self) -> None:
        self.session = FakeSession()
        self.clicks = []
        self.events = []

    async def create_buy_click(self, **kwargs):
        click = SimpleNamespace(id=uuid4())
        self.clicks.append((click, kwargs))
        return click

    async def create_event(self, **kwargs):
        self.events.append(kwargs)
        return SimpleNamespace(**kwargs)


class FakeAffiliate:
    def build_redirect(self, **kwargs):
        return AffiliateRedirect(
            redirect_url="https://merchant.example/p/1?afa_click_id=" + kwargs["tracking_id"],
            affiliate_network="mvp",
            tracking_id=kwargs["tracking_id"],
        )


@pytest.mark.asyncio
async def test_create_buy_click_uses_trusted_offer_url_and_writes_event(monkeypatch):
    @asynccontextmanager
    async def noop_transaction(session):
        yield session

    monkeypatch.setattr(commerce_module, "transaction", noop_transaction)

    garment_id = uuid4()
    offer_id = uuid4()
    offer = SimpleNamespace(id=offer_id, garment_id=garment_id, merchant_id=uuid4(), url="https://merchant.example/p/1", in_stock=True)
    commerce = FakeCommerce()
    service = CommerceService(commerce=commerce, catalog=FakeCatalog(offer), affiliate=FakeAffiliate())

    result = await service.create_buy_click(
        user_id=uuid4(),
        request=BuyClickCreate(garment_id=garment_id, offer_id=offer_id),
        trace_id=uuid4(),
    )

    assert result.offer_id == offer_id
    assert result.redirect_url.startswith("https://merchant.example/")
    assert commerce.clicks
    assert commerce.events[0]["event_type"] == "buy_clicked"
