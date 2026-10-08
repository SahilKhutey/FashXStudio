from __future__ import annotations

from uuid import uuid4

from fastapi.routing import APIRoute

from api.app.main import app
from schemas.catalog.detail import CatalogDetail, CatalogImageView, CatalogOfferView, SaveCatalogItemRequest


def route_paths() -> set[str]:
    return {route.path for route in app.routes if isinstance(route, APIRoute)}


def test_foundation_11_product_routes_registered() -> None:
    paths = route_paths()
    assert "/api/v1/catalog/{product_id}" in paths
    assert "/api/v1/catalog/{product_id}/select-offer" in paths
    assert "/api/v1/wardrobe/save/{product_id}" in paths
    assert "/api/v1/wardrobe/reject/{product_id}" in paths


def test_catalog_detail_contract_supports_signed_image_views() -> None:
    garment_id = uuid4()
    payload = CatalogDetail(
        garment={
            "id": garment_id,
            "brand_id": None,
            "display_name": "Demo Shirt",
            "category": "shirt",
            "subcategory": "casual",
            "version": 1,
        },
        images=[CatalogImageView(id=str(uuid4()), image_type="front", url="https://example.test/image", version=1)],
        offers=[CatalogOfferView(
            id=str(uuid4()), merchant_id=str(uuid4()), source_product_id="demo-1",
            url="https://merchant.test/p/1", price_minor=129900, currency="INR", in_stock=True, selected=True,
        )],
        selected_offer_id=None,
    )
    assert payload.images[0].url == "https://example.test/image"
    assert payload.offers[0].selected is True


def test_save_contract_defaults_to_no_offer() -> None:
    request = SaveCatalogItemRequest()
    assert request.offer_id is None
