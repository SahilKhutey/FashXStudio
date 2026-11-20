from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaxonomyCategoryNode:
    id: str
    label: str
    parent_id: str | None
    path: str
    description: str | None = None
    children_ids: list[str] = field(default_factory=list)
    is_leaf: bool = True


@dataclass
class TaxonomyRegistry:
    version: str
    categories: dict[str, TaxonomyCategoryNode]
    garment_types: dict[str, dict[str, Any]]
    occasions: dict[str, dict[str, Any]]
    audiences: dict[str, dict[str, Any]]
    color_families: dict[str, dict[str, Any]]
    color_shades: dict[str, str]  # shade_id -> family_id
    patterns: dict[str, dict[str, Any]]
    materials: dict[str, dict[str, Any]]
    sleeves: dict[str, dict[str, Any]]
    necklines: dict[str, dict[str, Any]]
    collars: dict[str, dict[str, Any]]
    fits: dict[str, dict[str, Any]]
    silhouettes: dict[str, dict[str, Any]]
    indian_wear: dict[str, Any]
    western_wear: dict[str, Any]
    footwear: dict[str, Any]
    accessories: dict[str, Any]
    missing_values: dict[str, Any]
    aliases: dict[str, tuple[str, str]] = field(default_factory=dict)

    # 1. Category query and hierarchy methods
    def is_valid_category(self, category_id: str) -> bool:
        return category_id in self.categories

    def get_category(self, category_id: str) -> TaxonomyCategoryNode | None:
        return self.categories.get(category_id)

    def is_leaf_category(self, category_id: str) -> bool:
        cat = self.get_category(category_id)
        return cat.is_leaf if cat else False

    def get_category_path(self, category_id: str) -> list[str]:
        path: list[str] = []
        curr: str | None = category_id
        while curr:
            node = self.categories.get(curr)
            if not node:
                break
            path.append(node.id)
            curr = node.parent_id
        path.reverse()
        return path

    def get_children_categories(self, category_id: str) -> list[str]:
        cat = self.get_category(category_id)
        return list(cat.children_ids) if cat else []

    # 2. Garment types
    def is_valid_garment_type(self, garment_type_id: str, category_id: str | None = None) -> bool:
        if garment_type_id not in self.garment_types:
            return False
        if category_id is None:
            return True
        info = self.garment_types[garment_type_id]
        allowed = info.get("allowed_categories", [])
        if not allowed:
            return True
        # Check if category_id or any of its ancestors match allowed_categories
        path = self.get_category_path(category_id)
        return any(cat in allowed for cat in path)

    def get_allowed_garment_types(self, category_id: str) -> list[str]:
        path = self.get_category_path(category_id)
        results: list[str] = []
        for g_id, info in self.garment_types.items():
            allowed = info.get("allowed_categories", [])
            if any(cat in allowed for cat in path):
                results.append(g_id)
        return results

    # 3. Vocabularies
    def is_valid_occasion(self, occasion_id: str) -> bool:
        return occasion_id in self.occasions

    def is_valid_audience(self, audience_id: str) -> bool:
        return audience_id in self.audiences

    def is_valid_color(self, color_id: str) -> bool:
        return color_id in self.color_shades or color_id in self.color_families

    def get_color_family(self, color_id: str) -> str | None:
        if color_id in self.color_families:
            return color_id
        return self.color_shades.get(color_id)

    def is_valid_pattern(self, pattern_id: str) -> bool:
        return pattern_id in self.patterns

    def is_valid_material(self, material_id: str) -> bool:
        return material_id in self.materials

    def is_valid_sleeve(self, sleeve_id: str) -> bool:
        return sleeve_id in self.sleeves

    def is_valid_neckline(self, neckline_id: str) -> bool:
        return neckline_id in self.necklines or neckline_id in self.collars

    def is_valid_fit(self, fit_id: str) -> bool:
        return fit_id in self.fits

    def is_valid_silhouette(self, silhouette_id: str) -> bool:
        return silhouette_id in self.silhouettes

    # 4. Attribute applicability
    def is_attribute_applicable(self, category_id: str, attribute_name: str) -> bool:
        path = self.get_category_path(category_id)
        root = path[0] if path else category_id

        # Non-garments (accessories, footwear) do NOT accept necklines or sleeves
        if root in {"accessories", "footwear"}:
            if attribute_name in {"sleeve", "sleeve_type", "neckline", "neckline_type", "collar"}:
                return False

        # Accessories do not accept garment fit or silhouettes
        if root == "accessories":
            if attribute_name in {"fit", "fit_type", "silhouette", "waist_rise", "kurta_length"}:
                return False

        # Bottoms (jeans, trousers, skirts, shorts) do NOT accept necklines or sleeves
        if "apparel_bottoms" in path or any("bottom" in p for p in path):
            if attribute_name in {"sleeve", "sleeve_type", "neckline", "neckline_type", "collar"}:
                return False

        # Sarees do not have sleeves or necklines (blouses are separate)
        if "ethnic_wear_sarees" in path:
            if attribute_name in {"sleeve", "sleeve_type", "neckline", "neckline_type", "collar"}:
                return False

        return True

    # 5. Synonym / Alias lookup
    def resolve_alias(self, term: str, target_type: str | None = None) -> tuple[str, str] | None:
        """Resolve a merchant term / synonym to (target_type, canonical_id)."""
        normalized = term.strip().lower()
        if normalized in self.aliases:
            res_type, res_id = self.aliases[normalized]
            if target_type is None or res_type == target_type:
                return res_type, res_id
        return None
