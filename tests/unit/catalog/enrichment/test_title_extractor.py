from __future__ import annotations

from fashx.catalog.enrichment.title_extractor import extract_title_attributes


def values_for(title: str, attribute: str) -> list[str]:
    return [item.value for item in extract_title_attributes(title) if item.attribute_id == attribute]


def test_enr_005_extract_garment_type_from_title() -> None:
    """Verify ENR-005: Extract correct taxonomy garment types from diverse title phrases."""
    assert values_for("Men's Black Cotton T-Shirt", "garment_type") == ["t_shirt"]
    assert values_for("Women's Floral Casual Shirt", "garment_type") == ["casual_shirt"]
    assert values_for("Classic Striped Polo Tee", "garment_type") == ["polo_shirt"]
    assert values_for("Men's Ethnic Short Kurta", "garment_type") == ["kurta"]
    assert values_for("Printed Cotton Kurti", "garment_type") == ["kurti"]
    assert values_for("Slim Fit Distressed Jeans", "garment_type") == ["jeans"]
    assert values_for("Casual White Sneakers", "garment_type") == ["sneakers"]


def test_enr_006_extract_fit_from_title() -> None:
    """Verify ENR-006: Extract correct fit from product title."""
    assert values_for("Oversized Graphic T-Shirt", "fit_type") == ["oversized"]
    assert values_for("Slim Fit Business Shirt", "fit_type") == ["slim"]
    assert values_for("Regular Fit Crew Neck Tee", "fit_type") == ["regular"]
    assert values_for("Women's High Rise Wide Leg Jeans", "fit_type") == ["wide_leg"]


def test_enr_007_extract_color_from_title() -> None:
    """Verify ENR-007: Extract normalized colors from title."""
    assert values_for("Navy Blue Casual Shirt", "color") == ["navy"]
    assert values_for("Off-White Cotton Kurta", "color") == ["off_white"]
    assert values_for("Pure Black Round Neck Tee", "color") == ["black"]
    assert values_for("Olive Green Field Jacket", "color") == ["olive"]


def test_enr_008_extract_pattern_from_title() -> None:
    """Verify ENR-008: Extract pattern vocabulary from title."""
    assert values_for("Men's Oversized Graphic Cotton T-Shirt", "pattern") == ["graphic"]
    assert values_for("Checked Casual Shirt", "pattern") == ["checked"]
    assert values_for("Striped Crew Neck Tee", "pattern") == ["striped"]
    assert values_for("Floral Printed Summer Top", "pattern") == ["floral"]
    assert values_for("Traditional Bandhani Silk Kurti", "pattern") == ["bandhani"]


def test_enr_009_extract_occasion_from_title() -> None:
    """Verify ENR-009: Extract occasion when supported by evidence in title."""
    assert values_for("Casual Everyday Cotton Shirt", "occasion") == ["casual"]
    assert values_for("Men's Formal Office Shirt", "occasion") == ["formal"]
    assert values_for("Festive Embroidered Kurta", "occasion") == ["festive"]
    assert values_for("Running Sports Tee", "occasion") == ["sports"]
