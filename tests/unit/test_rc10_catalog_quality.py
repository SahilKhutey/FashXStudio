from datetime import UTC, datetime

from scripts.rc10.evaluate_catalog import evaluate_product


def valid_product():
    return {
        "merchant_id": "merchant-test",
        "source_product_id": "product-test",
        "canonical_product_id": "canonical-test",
        "category": "kurta",
        "image_reference": "private-object-reference",
        "source_clearance": True,
        "price": 1299,
        "currency": "INR",
        "price_updated_at": "2026-11-05T04:00:00+00:00",
    }


def test_valid_catalog_product_passes():
    clock = datetime(2026, 11, 5, 5, 0, 0, tzinfo=UTC)
    result = evaluate_product(valid_product(), reference_time=clock)
    assert result.passed
    assert result.score == 1.0
    assert not result.errors


def test_uncleared_source_fails():
    product = valid_product()
    product["source_clearance"] = False
    result = evaluate_product(product)
    assert not result.passed
    assert "source_not_cleared" in result.errors


def test_missing_image_fails():
    product = valid_product()
    product["image_reference"] = None
    result = evaluate_product(product)
    assert not result.passed
    assert "missing_image" in result.errors


def test_stale_price_fails():
    product = valid_product()
    product["price_updated_at"] = "2026-11-01T00:00:00+00:00"
    clock = datetime(2026, 11, 5, 5, 0, 0, tzinfo=UTC)
    result = evaluate_product(product, reference_time=clock)
    assert not result.passed
    assert "stale_price" in result.errors


def test_invalid_price_fails():
    product = valid_product()
    product["price"] = -10
    result = evaluate_product(product)
    assert not result.passed
    assert "invalid_price" in result.errors
