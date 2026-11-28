from __future__ import annotations

import pytest

from fashx.catalog.detail.redirect_validator import validate_merchant_url
from fashx.catalog.detail.schemas import (
    AttributeSource,
    ProductAttributeResponse,
    ProductAvailability,
)


def test_validate_merchant_url_allows_verified_https_domains() -> None:
    url = validate_merchant_url(
        "https://shop.merchant.example/products/123",
        {"merchant.example"},
    )
    assert url == "https://shop.merchant.example/products/123"


@pytest.mark.parametrize(
    "bad_url",
    [
        "http://merchant.example/products/123",
        "javascript:alert(1)",
        "https://user:pass@merchant.example/products/123",
        "https://evil-merchant.example/products/123",
        "https://merchant.example.attacker.com/products/123",
        "",
    ],
)
def test_validate_merchant_url_rejects_unsafe_or_unverified_urls(bad_url: str) -> None:
    with pytest.raises(ValueError):
        validate_merchant_url(bad_url, {"merchant.example"})


def test_pdp_attribute_provenance_and_availability_enum() -> None:
    attr = ProductAttributeResponse(
        key="material",
        label="Material",
        value="Cotton",
        source=AttributeSource.MERCHANT,
    )
    assert attr.source == AttributeSource.MERCHANT
    assert ProductAvailability.UNKNOWN.value == "unknown"
    assert ProductAvailability.TAKEN_DOWN.value == "taken_down"
