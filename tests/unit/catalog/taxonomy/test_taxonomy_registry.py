from __future__ import annotations

from fashx.catalog.taxonomy.loader import get_taxonomy_registry


def test_garment_types_mapping() -> None:
    """Verify TAX-003: Garment types exist and map to appropriate categories."""
    registry = get_taxonomy_registry()

    assert registry.is_valid_garment_type("t_shirt")
    assert registry.is_valid_garment_type("kurta")
    assert registry.is_valid_garment_type("sneakers")
    assert not registry.is_valid_garment_type("spacesuit")

    # Category compatibility
    assert registry.is_valid_garment_type("t_shirt", "apparel_tops_t_shirts")
    assert not registry.is_valid_garment_type("t_shirt", "footwear_sneakers")
    assert registry.is_valid_garment_type("kurta", "ethnic_wear_kurtas_and_kurtis")
    assert not registry.is_valid_garment_type("kurta", "apparel_bottoms_jeans")


def test_occasion_vocabulary() -> None:
    """Verify TAX-004: Standard occasions exist."""
    registry = get_taxonomy_registry()
    for occ in ["everyday", "casual", "workwear", "wedding", "festive", "sports"]:
        assert registry.is_valid_occasion(occ), f"Occasion {occ} should be valid"
    assert not registry.is_valid_occasion("outer_space")


def test_intended_audience_vocabulary() -> None:
    """Verify TAX-005: Intended audience vocabularies exist."""
    registry = get_taxonomy_registry()
    for aud in ["men", "women", "unisex", "kids", "unknown"]:
        assert registry.is_valid_audience(aud), f"Audience {aud} should be valid"
    assert not registry.is_valid_audience("alien")


def test_color_and_family_resolution() -> None:
    """Verify TAX-006: Color families and shades resolve correctly."""
    registry = get_taxonomy_registry()

    assert registry.is_valid_color("navy")
    assert registry.get_color_family("navy") == "blue"

    assert registry.is_valid_color("charcoal")
    assert registry.get_color_family("charcoal") == "black"

    assert registry.is_valid_color("ivory")
    assert registry.get_color_family("ivory") == "white"

    assert registry.is_valid_color("maroon")
    assert registry.get_color_family("maroon") == "red"

    assert not registry.is_valid_color("ultraviolet_neon_xyz")


def test_pattern_vocabulary() -> None:
    """Verify TAX-007: Universal and Indian craftsmanship patterns exist."""
    registry = get_taxonomy_registry()
    universal = ["solid", "striped", "checked", "floral", "graphic", "embroidered"]
    for pat in universal:
        assert registry.is_valid_pattern(pat), f"Pattern {pat} should be valid"

    indian_craft = ["block_print", "bandhani", "chikankari", "phulkari", "zari_work"]
    for pat in indian_craft:
        assert registry.is_valid_pattern(pat), f"Indian craft pattern {pat} should be valid"

    assert not registry.is_valid_pattern("pixelated_laser")


def test_fabric_material_vocabulary() -> None:
    """Verify TAX-008: Fabric materials exist."""
    registry = get_taxonomy_registry()
    for mat in ["cotton", "linen", "silk", "wool", "polyester", "denim", "rayon"]:
        assert registry.is_valid_material(mat), f"Material {mat} should be valid"
    assert not registry.is_valid_material("unobtainium")


def test_sleeves_necklines_and_silhouettes() -> None:
    """Verify TAX-009 & TAX-010: Construction, sleeve, neckline, and fit attributes."""
    registry = get_taxonomy_registry()

    for slv in ["sleeveless", "short_sleeve", "full_sleeve", "three_quarter_sleeve"]:
        assert registry.is_valid_sleeve(slv), f"Sleeve {slv} should be valid"

    for nck in ["crew_neck", "v_neck", "round_neck", "collared", "mandarin_collar"]:
        assert registry.is_valid_neckline(nck), f"Neckline {nck} should be valid"

    for fit in ["regular", "slim", "relaxed", "oversized"]:
        assert registry.is_valid_fit(fit), f"Fit {fit} should be valid"

    for sil in ["straight", "a_line", "fit_and_flare", "bodycon"]:
        assert registry.is_valid_silhouette(sil), f"Silhouette {sil} should be valid"


def test_attribute_applicability_rules() -> None:
    """Verify category-specific attribute applicability (e.g. no neckline on handbag)."""
    registry = get_taxonomy_registry()

    # Tops accept sleeves and necklines
    assert registry.is_attribute_applicable("apparel_tops_t_shirts", "sleeve_type")
    assert registry.is_attribute_applicable("apparel_tops_t_shirts", "neckline")

    # Bottoms do NOT accept sleeves or necklines
    assert not registry.is_attribute_applicable("apparel_bottoms_jeans", "neckline")
    assert not registry.is_attribute_applicable("apparel_bottoms_jeans", "sleeve_type")

    # Footwear does NOT accept necklines or sleeves
    assert not registry.is_attribute_applicable("footwear_sneakers", "neckline")
    assert not registry.is_attribute_applicable("footwear_sneakers", "sleeve_type")

    # Bags do NOT accept necklines, sleeves, or fits
    assert not registry.is_attribute_applicable("accessories_bags", "neckline")
    assert not registry.is_attribute_applicable("accessories_bags", "fit")


def test_alias_resolution() -> None:
    """Verify merchant terminology and synonyms resolve to canonical taxonomy IDs."""
    registry = get_taxonomy_registry()

    res = registry.resolve_alias("tee", "garment_type")
    assert res == ("garment_type", "t_shirt")

    res = registry.resolve_alias("kurti", "garment_type")
    assert res == ("garment_type", "kurti")

    res = registry.resolve_alias("round neck", "neckline")
    assert res == ("neckline", "round_neck")

    res = registry.resolve_alias("half sleeve", "sleeve")
    assert res == ("sleeve", "half_sleeve")
