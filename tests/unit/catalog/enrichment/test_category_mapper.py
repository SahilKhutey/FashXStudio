from __future__ import annotations

from fashx.catalog.enrichment.category_mapper import map_merchant_category
from fashx.catalog.taxonomy.loader import get_taxonomy_registry


def test_map_known_merchant_categories() -> None:
    """Verify mapping of standard merchant category strings into taxonomy leaf nodes."""
    reg = get_taxonomy_registry()

    res1 = map_merchant_category("Men's Clothing / T-shirts", reg)
    assert res1.category_id == "apparel_tops_t_shirts"
    assert res1.is_leaf is True
    assert res1.quarantined is False

    res2 = map_merchant_category("Men / Casual Shirts", reg)
    assert res2.category_id == "apparel_tops_shirts"
    assert res2.is_leaf is True
    assert res2.quarantined is False

    res3 = map_merchant_category("Ethnic Wear / Men's Kurtas", reg)
    assert res3.category_id == "ethnic_wear_kurtas_and_kurtis"
    assert res3.is_leaf is True
    assert res3.quarantined is False

    res4 = map_merchant_category("Footwear / Sneakers", reg)
    assert res4.category_id == "footwear_sneakers"
    assert res4.is_leaf is True
    assert res4.quarantined is False


def test_enr_010_unknown_category_quarantined() -> None:
    """Verify ENR-010: Unrecognized category is quarantined and never defaulted to tops/shirts."""
    reg = get_taxonomy_registry()

    res = map_merchant_category("Unmatched Alien Category 999", reg)
    assert res.category_id is None
    assert res.quarantined is True
    assert res.ambiguity_reason == "UNRESOLVED_CATEGORY_QUARANTINED"
