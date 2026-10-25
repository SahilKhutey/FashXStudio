from fashx.catalog.quality.quality_gate import CatalogQualityGate


def test_catalog_quality_gate_passes_complete_batch() -> None:
    items = [
        {
            "category": "tops",
            "attributes": {"silhouette": "slim", "dominant_color": "navy", "formality": "casual"},
            "price_minor": 199900,
            "in_stock": True,
            "image_url": "https://example.com/img.jpg",
            "image_rights": "owned",
        }
        for _ in range(100)
    ]
    report = CatalogQualityGate.audit_garment_batch(items)
    assert report.passed_gate is True
    assert report.completeness_score == 1.0
    assert report.category_validity == 1.0
    assert report.silhouette_validity == 1.0
    assert report.color_validity == 1.0
    assert len(report.issues) == 0


def test_catalog_quality_gate_fails_on_missing_attributes() -> None:
    items = [
        {
            "category": "invalid_category",
            "attributes": {},
            "price_minor": 0,
        }
        for _ in range(50)
    ]
    report = CatalogQualityGate.audit_garment_batch(items)
    assert report.passed_gate is False
    assert report.completeness_score == 0.0
    assert report.category_validity == 0.0
    assert len(report.issues) > 0


def test_catalog_quality_gate_fails_on_empty_batch() -> None:
    """An empty batch must fail closed and cannot be passed as production-ready."""
    report = CatalogQualityGate.audit_garment_batch([])
    assert report.passed_gate is False
    assert report.total_garments == 0
    assert report.completeness_score == 0.0
    assert len(report.issues) > 0
    assert any("Empty catalog batch cannot pass" in issue for issue in report.issues)


def test_catalog_quality_gate_individual_item_eligibility() -> None:
    valid_item = {
        "category": "tops",
        "price_minor": 149900,
        "in_stock": True,
        "image_url": "https://images.fashx.studio/products/shirt-001.jpg",
        "image_rights": "owned",
        "source_status": "cleared",
    }
    is_eligible, issues = CatalogQualityGate.is_item_eligible(valid_item)
    assert is_eligible is True
    assert len(issues) == 0

    # Ineligible item: unapproved source
    ineligible_item = {
        **valid_item,
        "source_status": "pending_approval",
    }
    is_eligible_unapproved, unapproved_issues = CatalogQualityGate.is_item_eligible(ineligible_item)
    assert is_eligible_unapproved is False
    assert any("not cleared" in issue for issue in unapproved_issues)

    # Ineligible item: zero price and out of stock
    zero_price_item = {
        **valid_item,
        "price_minor": 0,
        "in_stock": False,
    }
    is_eligible_zero, zero_issues = CatalogQualityGate.is_item_eligible(zero_price_item)
    assert is_eligible_zero is False
    assert any("price_minor" in issue for issue in zero_issues)
    assert any("out of stock" in issue for issue in zero_issues)
