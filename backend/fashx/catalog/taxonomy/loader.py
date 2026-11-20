from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .registry import TaxonomyCategoryNode, TaxonomyRegistry

logger = logging.getLogger("fashx.catalog.taxonomy.loader")

_DEFAULT_SCHEMAS_PATH = Path(__file__).resolve().parent / "schemas"
_REGISTRY_CACHE: TaxonomyRegistry | None = None


class TaxonomyLoadError(ValueError):
    """Raised when taxonomy schema files are invalid or fail structural constraints."""
    pass


class TaxonomyLoader:
    """Loads and compiles versioned fashion taxonomy YAML schemas into an in-memory TaxonomyRegistry."""

    def __init__(self, schemas_dir: str | Path | None = None) -> None:
        self.schemas_dir = Path(schemas_dir) if schemas_dir else _DEFAULT_SCHEMAS_PATH

    def load(self) -> TaxonomyRegistry:
        if not self.schemas_dir.exists():
            raise TaxonomyLoadError(f"Taxonomy schemas directory not found: {self.schemas_dir}")

        # 1. Load categories
        category_file = self.schemas_dir / "category.yaml"
        if not category_file.exists():
            raise TaxonomyLoadError(f"Missing category.yaml in {self.schemas_dir}")
        category_data = self._read_yaml(category_file)
        version = str(category_data.get("version", "1.0.0"))
        raw_categories = category_data.get("categories", [])
        categories = self._compile_categories(raw_categories)

        # 2. Load garment types
        garment_types_data = self._read_yaml(self.schemas_dir / "garment_types.yaml")
        garment_types = garment_types_data.get("garment_types", {})

        # 3. Load occasions
        occasions_data = self._read_yaml(self.schemas_dir / "occasions.yaml")
        occasions = occasions_data.get("occasions", {})

        # 4. Load audiences
        audiences_data = self._read_yaml(self.schemas_dir / "audiences.yaml")
        audiences = audiences_data.get("audiences", {})

        # 5. Load colors
        colors_data = self._read_yaml(self.schemas_dir / "colors.yaml")
        color_families = colors_data.get("color_families", {})
        color_shades: dict[str, str] = {}
        for family_id, fam_info in color_families.items():
            for shade in fam_info.get("shades", []):
                shade_id = shade.get("id")
                if shade_id:
                    color_shades[shade_id] = family_id

        # 6. Load patterns
        patterns_data = self._read_yaml(self.schemas_dir / "patterns.yaml")
        patterns = patterns_data.get("patterns", {})

        # 7. Load fabrics / materials
        fabrics_data = self._read_yaml(self.schemas_dir / "fabrics.yaml")
        materials = fabrics_data.get("materials", {})

        # 8. Load sleeves
        sleeves_data = self._read_yaml(self.schemas_dir / "sleeves.yaml")
        sleeves = sleeves_data.get("sleeves", {})

        # 9. Load necklines and collars
        necklines_data = self._read_yaml(self.schemas_dir / "necklines.yaml")
        necklines = necklines_data.get("necklines", {})
        collars = necklines_data.get("collars", {})

        # 10. Load silhouettes and fits
        silhouettes_data = self._read_yaml(self.schemas_dir / "silhouettes.yaml")
        fits = silhouettes_data.get("fits", {})
        silhouettes = silhouettes_data.get("silhouettes", {})

        # 11. Extensions
        indian_wear = self._read_yaml(self.schemas_dir / "indian_wear.yaml").get("indian_wear", {})
        western_wear = self._read_yaml(self.schemas_dir / "western_wear.yaml").get("western_wear", {})
        footwear = self._read_yaml(self.schemas_dir / "footwear.yaml").get("footwear", {})
        accessories = self._read_yaml(self.schemas_dir / "accessories.yaml").get("accessories", {})
        missing_values = self._read_yaml(self.schemas_dir / "missing_values.yaml").get("missing_values", {})

        # 12. Build initial merchant aliases / synonyms
        aliases = self._build_default_aliases()

        registry = TaxonomyRegistry(
            version=version,
            categories=categories,
            garment_types=garment_types,
            occasions=occasions,
            audiences=audiences,
            color_families=color_families,
            color_shades=color_shades,
            patterns=patterns,
            materials=materials,
            sleeves=sleeves,
            necklines=necklines,
            collars=collars,
            fits=fits,
            silhouettes=silhouettes,
            indian_wear=indian_wear,
            western_wear=western_wear,
            footwear=footwear,
            accessories=accessories,
            missing_values=missing_values,
            aliases=aliases,
        )

        logger.info(
            f"Successfully compiled fashion taxonomy v{version} with "
            f"{len(categories)} categories, {len(garment_types)} garment types, "
            f"{len(materials)} materials, {len(patterns)} patterns."
        )
        return registry

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
                return content if isinstance(content, dict) else {}
        except Exception as e:
            raise TaxonomyLoadError(f"Failed to parse YAML file {path}: {e}") from e

    def _compile_categories(self, raw_nodes: list[dict[str, Any]]) -> dict[str, TaxonomyCategoryNode]:
        nodes: dict[str, TaxonomyCategoryNode] = {}

        def _traverse(node: dict[str, Any], parent_id: str | None, current_path: str) -> None:
            node_id = str(node["id"])
            if node_id in nodes:
                raise TaxonomyLoadError(f"Duplicate category ID detected: {node_id}")

            path = f"{current_path}/{node_id}" if current_path else node_id
            children_raw = node.get("children", [])
            children_ids = [str(c["id"]) for c in children_raw]

            cat_node = TaxonomyCategoryNode(
                id=node_id,
                label=str(node.get("label", node_id)),
                parent_id=parent_id,
                path=path,
                description=node.get("description"),
                children_ids=children_ids,
                is_leaf=len(children_ids) == 0,
            )
            nodes[node_id] = cat_node

            for child in children_raw:
                _traverse(child, node_id, path)

        for root in raw_nodes:
            _traverse(root, None, "")

        # Verify parent references and ensure no cyclic references
        for node_id, node in nodes.items():
            if node.parent_id and node.parent_id not in nodes:
                raise TaxonomyLoadError(f"Invalid parent ID '{node.parent_id}' for category '{node_id}'")

            # Check cycle by walking up
            visited = {node_id}
            curr = node.parent_id
            while curr:
                if curr in visited:
                    raise TaxonomyLoadError(f"Cycle detected in taxonomy category hierarchy at '{curr}'")
                visited.add(curr)
                curr = nodes[curr].parent_id

        return nodes

    def _build_default_aliases(self) -> dict[str, tuple[str, str]]:
        """Common merchant synonyms and aliases mapped to canonical identifiers."""
        return {
            # Garment types
            "tee": ("garment_type", "t_shirt"),
            "tshirt": ("garment_type", "t_shirt"),
            "t-shirt": ("garment_type", "t_shirt"),
            "polo": ("garment_type", "polo_shirt"),
            "polo tee": ("garment_type", "polo_shirt"),
            "shirt": ("garment_type", "casual_shirt"),
            "short kurta": ("garment_type", "short_kurta"),
            "kurti": ("garment_type", "kurti"),
            "kurta": ("garment_type", "kurta"),
            "sari": ("garment_type", "saree"),
            "jean": ("garment_type", "jeans"),
            "denims": ("garment_type", "jeans"),
            "trouser": ("garment_type", "trousers"),
            "pant": ("garment_type", "trousers"),
            "pants": ("garment_type", "trousers"),
            "shoe": ("garment_type", "formal_shoes"),
            "shoes": ("garment_type", "formal_shoes"),
            "sneaker": ("garment_type", "sneakers"),
            # Necklines
            "crew": ("neckline", "crew_neck"),
            "crewneck": ("neckline", "crew_neck"),
            "crew neck": ("neckline", "crew_neck"),
            "round neck": ("neckline", "round_neck"),
            "round-neck": ("neckline", "round_neck"),
            "v neck": ("neckline", "v_neck"),
            "v-neck": ("neckline", "v_neck"),
            "mandarin": ("neckline", "mandarin_collar"),
            "band collar": ("neckline", "band_collar"),
            # Sleeves
            "half sleeve": ("sleeve", "half_sleeve"),
            "half sleeves": ("sleeve", "half_sleeve"),
            "short sleeve": ("sleeve", "short_sleeve"),
            "short sleeves": ("sleeve", "short_sleeve"),
            "full sleeve": ("sleeve", "full_sleeve"),
            "full sleeves": ("sleeve", "full_sleeve"),
            "long sleeve": ("sleeve", "long_sleeve"),
            "sleeveless": ("sleeve", "sleeveless"),
            # Fits
            "regular fit": ("fit", "regular"),
            "slim fit": ("fit", "slim"),
            "relaxed fit": ("fit", "relaxed"),
            "oversized fit": ("fit", "oversized"),
        }


def get_taxonomy_registry(force_reload: bool = False) -> TaxonomyRegistry:
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is None or force_reload:
        loader = TaxonomyLoader()
        _REGISTRY_CACHE = loader.load()
    return _REGISTRY_CACHE
