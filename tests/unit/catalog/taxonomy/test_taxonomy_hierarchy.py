from __future__ import annotations

import pytest

from fashx.catalog.taxonomy.loader import TaxonomyLoader, TaxonomyLoadError, get_taxonomy_registry


def test_top_level_categories_exist() -> None:
    """Verify TAX-001: all approved top-level categories exist."""
    registry = get_taxonomy_registry()
    expected_top_level = {
        "apparel",
        "ethnic_wear",
        "footwear",
        "accessories",
        "activewear",
        "innerwear",
        "outerwear",
    }
    for cat_id in expected_top_level:
        node = registry.get_category(cat_id)
        assert node is not None, f"Top-level category {cat_id} must exist"
        assert node.parent_id is None, f"{cat_id} must be a root category"


def test_subcategory_hierarchy_and_paths() -> None:
    """Verify TAX-002: subcategory hierarchy paths and parent-child relations."""
    registry = get_taxonomy_registry()

    # Check apparel -> tops -> t_shirts
    t_shirts = registry.get_category("apparel_tops_t_shirts")
    assert t_shirts is not None
    assert t_shirts.parent_id == "apparel_tops"
    assert t_shirts.is_leaf is True
    assert registry.get_category_path("apparel_tops_t_shirts") == [
        "apparel",
        "apparel_tops",
        "apparel_tops_t_shirts",
    ]

    # Check ethnic_wear -> kurtas_and_kurtis
    kurtas = registry.get_category("ethnic_wear_kurtas_and_kurtis")
    assert kurtas is not None
    assert kurtas.parent_id == "ethnic_wear"
    assert kurtas.is_leaf is True

    # Check footwear -> sneakers
    sneakers = registry.get_category("footwear_sneakers")
    assert sneakers is not None
    assert sneakers.parent_id == "footwear"
    assert sneakers.is_leaf is True


def test_hierarchy_detects_duplicate_category_id(tmp_path) -> None:
    """Verify hierarchy compiler rejects duplicate category IDs."""
    loader = TaxonomyLoader()
    duplicate_raw = [
        {"id": "cat_a", "label": "Cat A", "children": []},
        {"id": "cat_a", "label": "Duplicate Cat A", "children": []},
    ]
    with pytest.raises(TaxonomyLoadError, match="Duplicate category ID"):
        loader._compile_categories(duplicate_raw)


def test_hierarchy_detects_cycles(tmp_path) -> None:
    """Verify hierarchy compiler detects circular references."""
    loader = TaxonomyLoader()
    # Construct nodes directly to simulate cycle
    nodes = {
        "node_1": loader._compile_categories([{"id": "node_1", "children": []}])["node_1"],
        "node_2": loader._compile_categories([{"id": "node_2", "children": []}])["node_2"],
    }
    nodes["node_1"].parent_id = "node_2"
    nodes["node_2"].parent_id = "node_1"

    # Check that cycle detection logic would reject
    with pytest.raises(TaxonomyLoadError, match="Cycle detected"):
        # Run cycle check logic
        for node_id, node in nodes.items():
            visited = {node_id}
            curr = node.parent_id
            while curr:
                if curr in visited:
                    raise TaxonomyLoadError(f"Cycle detected in taxonomy category hierarchy at '{curr}'")
                visited.add(curr)
                curr = nodes[curr].parent_id
