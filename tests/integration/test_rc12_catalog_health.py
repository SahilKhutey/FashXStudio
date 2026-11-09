from datetime import UTC, datetime

from scripts.rc12.catalog_health import evaluate_catalog_records


def test_catalog_health_evaluates_counts():
    clock = datetime(2026, 11, 9, 12, 0, 0, tzinfo=UTC)
    sample_records = [
        {
            "source_product_id": "sp-1",
            "source_clearance": True,
            "image_reference": "img://sp-1.jpg",
            "price_updated_at": "2026-11-09T10:00:00Z",
            "in_stock": True,
            "is_new": True,
        },
        {
            "source_product_id": "sp-2",
            "source_clearance": False,  # Permission blocked
            "image_reference": "img://sp-2.jpg",
            "price_updated_at": "2026-11-09T10:00:00Z",
            "in_stock": True,
            "is_new": True,
        },
        {
            "source_product_id": "sp-3",
            "source_clearance": True,
            "image_reference": "img://sp-3.jpg",
            "price_updated_at": "2026-11-07T00:00:00Z",  # Stale (>24h)
            "in_stock": True,
            "is_new": False,
        },
        {
            "source_product_id": "sp-1",  # Duplicate candidate
            "source_clearance": True,
            "image_reference": "img://sp-1.jpg",
            "price_updated_at": "2026-11-09T11:00:00Z",
            "in_stock": True,
            "is_new": False,
        },
    ]

    report = evaluate_catalog_records(
        sample_records,
        source_name="partner_myntra",
        reference_time=clock,
    )

    assert report.total_fetched == 4
    assert report.duplicate_candidates == 1
    assert report.permission_blocked == 1
    assert report.stale_prices == 1
    assert report.published_products == 2
    assert "source_not_cleared" in report.rejected_by_reason
    assert "stale_price" in report.rejected_by_reason
