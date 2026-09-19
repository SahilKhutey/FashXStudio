from uuid import uuid4

from fastapi.testclient import TestClient

from api.app.auth.dependencies import current_user_id
from api.app.feed.router import get_service
from api.app.main import app


class FakeFeedService:
    async def get_feed(self, *, user_id, query):
        from schemas.catalog.search import CatalogItemSummary
        from schemas.feed.api import FeedItem, FeedResponse

        product = CatalogItemSummary(
            id=uuid4(),
            display_name="Demo Shirt",
            category="shirt",
            subcategory="casual",
            brand_id=None,
            version=1,
            primary_image_key="product-images/demo.webp",
            lowest_price_minor=129900,
            currency="INR",
            in_stock=True,
        )
        return FeedResponse(items=[FeedItem(product=product, reasons=["curated", "new_arrival"])])


def test_feed_contract():
    user_id = uuid4()
    app.dependency_overrides[current_user_id] = lambda: user_id
    app.dependency_overrides[get_service] = lambda: FakeFeedService()
    try:
        client = TestClient(app)
        response = client.get("/api/v1/feed/me", headers={"X-User-ID": str(user_id)})
        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["reasons"] == ["curated", "new_arrival"]
    finally:
        app.dependency_overrides.pop(current_user_id, None)
        app.dependency_overrides.pop(get_service, None)
