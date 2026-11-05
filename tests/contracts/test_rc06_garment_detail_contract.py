from uuid import uuid4

import pytest
from pydantic import ValidationError

from fashx.catalog.customer_router import (
    CustomerGarmentDetailResponse,
    CustomerOfferDetail,
)


def test_rc06_garment_detail_contract_valid():
    offer_id = uuid4()
    merchant_id = uuid4()
    garment_id = uuid4()

    offer = CustomerOfferDetail(
        id=offer_id,
        merchant_id=merchant_id,
        merchant_name="Myntra",
        source_product_id="SKU-100",
        url="https://myntra.com/p/100",
        price_minor=149900,
        currency="INR",
        in_stock=True,
    )

    detail = CustomerGarmentDetailResponse(
        id=garment_id,
        brand_name="Zara",
        title="Linen Blend Trousers",
        category="bottoms",
        subcategory="trousers",
        price_minor=149900,
        currency="INR",
        sizes_in_stock=["30", "32", "34"],
        tryon_supported=True,
        images=["https://images.example.com/item1.jpg"],
        offers=[offer],
    )

    data = detail.model_dump(mode="json")
    assert data["id"] == str(garment_id)
    assert data["brand_name"] == "Zara"
    assert data["price_minor"] == 149900
    assert data["currency"] == "INR"
    assert len(data["offers"]) == 1
    assert data["offers"][0]["merchant_name"] == "Myntra"
    assert data["offers"][0]["in_stock"] is True


def test_rc06_garment_detail_contract_extra_forbidden():
    with pytest.raises(ValidationError):
        CustomerGarmentDetailResponse(
            id=uuid4(),
            title="T-Shirt",
            category="tops",
            unknown_arbitrary_field="malicious_payload",  # Extra forbidden
        )


def test_rc06_offer_contract_extra_forbidden():
    with pytest.raises(ValidationError):
        CustomerOfferDetail(
            id=uuid4(),
            merchant_id=uuid4(),
            source_product_id="P1",
            url="https://store.com/1",
            price_minor=1000,
            currency="INR",
            in_stock=True,
            invented_field="disallowed",  # Extra forbidden
        )
