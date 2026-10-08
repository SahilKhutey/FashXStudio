from api.app.catalog.quality.quality_gate import CatalogQualityGate


def test_catalog_quality_gate_passes_complete_batch() -> None:
    items = [
        {
            "category": "tops",
            "attributes": {"silhouette": "slim", "dominant_color": "navy", "formality": "casual"},
            "price_minor": 199900,
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
