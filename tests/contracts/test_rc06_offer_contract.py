from datetime import datetime, timezone
from uuid import uuid4
import pytest
from pydantic import ValidationError

from fashx.catalog.customer_router import CustomerOfferDetail


def test_rc06_offer_contract_serialization():
    now = datetime.now(timezone.utc)
    offer = CustomerOfferDetail(
        id=uuid4(),
        merchant_id=uuid4(),
        merchant_name="Amazon India",
        source_product_id="B08N5WRWNW",
        url="https://amazon.in/dp/B08N5WRWNW",
        price_minor=89900,
        currency="INR",
        in_stock=True,
        updated_at=now,
    )

    serialized = offer.model_dump(mode="json")
    assert serialized["price_minor"] == 89900
    assert serialized["currency"] == "INR"
    assert serialized["in_stock"] is True
    assert serialized["merchant_name"] == "Amazon India"
    assert serialized["updated_at"] is not None


def test_rc06_offer_contract_missing_required_fields():
    with pytest.raises(ValidationError):
        CustomerOfferDetail(
            id=uuid4(),
            # missing merchant_id, source_product_id, url, price_minor, currency, in_stock
        )
