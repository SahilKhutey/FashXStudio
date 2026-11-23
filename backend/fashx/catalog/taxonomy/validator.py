from __future__ import annotations

from .contracts import (
    ProductClassification,
    TaxonomyAttributeValue,
    ValueStatus,
)
from .registry import TaxonomyRegistry


class TaxonomyValidationError(ValueError):
    """Raised when product taxonomy classification or attributes violate taxonomy constraints."""
    pass


class TaxonomyValidator:
    """Enforces taxonomy integrity, category-to-garment compatibility, and attribute applicability rules."""

    def __init__(self, registry: TaxonomyRegistry) -> None:
        self.registry = registry

    def validate(self, classification: ProductClassification, enforce_leaf: bool = True) -> None:
        # 1. Version check
        if classification.taxonomy_version != self.registry.version:
            raise TaxonomyValidationError(
                f"Taxonomy version mismatch: product has '{classification.taxonomy_version}', "
                f"registry requires '{self.registry.version}'"
            )

        # 2. Category check
        cat = self.registry.get_category(classification.category_id)
        if not cat:
            raise TaxonomyValidationError(f"Unknown taxonomy category: '{classification.category_id}'")

        if enforce_leaf and not cat.is_leaf:
            raise TaxonomyValidationError(
                f"Category '{classification.category_id}' is not a leaf category; "
                f"products must be classified into a specific subcategory (children: {cat.children_ids})"
            )

        # 3. Garment type check
        if classification.garment_type_id:
            if not self.registry.is_valid_garment_type(classification.garment_type_id):
                raise TaxonomyValidationError(
                    f"Unknown garment type: '{classification.garment_type_id}'"
                )
            if not self.registry.is_valid_garment_type(
                classification.garment_type_id, classification.category_id
            ):
                allowed = self.registry.get_allowed_garment_types(classification.category_id)
                raise TaxonomyValidationError(
                    f"Garment type '{classification.garment_type_id}' is incompatible with "
                    f"category '{classification.category_id}' (allowed garment types: {allowed})"
                )

        # 4. Audience check
        if classification.intended_audience:
            if not self.registry.is_valid_audience(classification.intended_audience):
                raise TaxonomyValidationError(
                    f"Invalid intended audience: '{classification.intended_audience}'"
                )

        # 5. Occasions check
        for occ in classification.occasions:
            if not self.registry.is_valid_occasion(occ):
                raise TaxonomyValidationError(f"Invalid occasion: '{occ}'")

        # 6. Attribute applicability and values check
        for attr_id, attr_val in classification.attributes.items():
            self._validate_attribute(classification.category_id, attr_id, attr_val)

        # 7. Category extension validation
        self._validate_extensions(classification)

    def _validate_attribute(
        self, category_id: str, attribute_id: str, attr_val: TaxonomyAttributeValue
    ) -> None:
        # Check applicability
        is_applicable = self.registry.is_attribute_applicable(category_id, attribute_id)
        if not is_applicable:
            if attr_val.status == ValueStatus.KNOWN and attr_val.value is not None:
                raise TaxonomyValidationError(
                    f"Attribute '{attribute_id}' is NOT APPLICABLE to category '{category_id}'"
                )
            return

        # If marked NOT_APPLICABLE on an applicable category, it should have null value
        if attr_val.status == ValueStatus.NOT_APPLICABLE and attr_val.value is not None:
            raise TaxonomyValidationError(
                f"Attribute '{attribute_id}' marked NOT_APPLICABLE cannot carry a non-null value"
            )

        # Check controlled values for known status
        if attr_val.status == ValueStatus.KNOWN and attr_val.value is not None:
            val_str = str(attr_val.value)
            if attribute_id in {"color", "primary_color"} and not self.registry.is_valid_color(val_str):
                raise TaxonomyValidationError(f"Invalid color value '{val_str}' for attribute '{attribute_id}'")
            elif attribute_id == "pattern" and not self.registry.is_valid_pattern(val_str):
                raise TaxonomyValidationError(f"Invalid pattern value '{val_str}' for attribute '{attribute_id}'")
            elif attribute_id in {"material", "fabric"} and not self.registry.is_valid_material(val_str):
                raise TaxonomyValidationError(f"Invalid material value '{val_str}' for attribute '{attribute_id}'")
            elif attribute_id in {"sleeve", "sleeve_type"} and not self.registry.is_valid_sleeve(val_str):
                raise TaxonomyValidationError(f"Invalid sleeve value '{val_str}' for attribute '{attribute_id}'")
            elif attribute_id in {"neckline", "neckline_type"} and not self.registry.is_valid_neckline(val_str):
                raise TaxonomyValidationError(f"Invalid neckline value '{val_str}' for attribute '{attribute_id}'")
            elif attribute_id in {"fit", "fit_type"} and not self.registry.is_valid_fit(val_str):
                raise TaxonomyValidationError(f"Invalid fit value '{val_str}' for attribute '{attribute_id}'")
            elif attribute_id == "silhouette" and not self.registry.is_valid_silhouette(val_str):
                raise TaxonomyValidationError(f"Invalid silhouette value '{val_str}' for attribute '{attribute_id}'")

    def _validate_extensions(self, classification: ProductClassification) -> None:
        path = self.registry.get_category_path(classification.category_id)
        root = path[0] if path else classification.category_id

        # Indian wear extension
        if classification.indian_wear:
            if root != "ethnic_wear":
                raise TaxonomyValidationError(
                    f"Indian wear attributes cannot be attached to non-ethnic category '{classification.category_id}'"
                )
            iw = classification.indian_wear
            if iw.kurta_length and iw.kurta_length not in self.registry.indian_wear.get("kurta_lengths", {}):
                raise TaxonomyValidationError(f"Invalid kurta length: '{iw.kurta_length}'")
            if iw.kurta_style and iw.kurta_style not in self.registry.indian_wear.get("kurta_styles", {}):
                raise TaxonomyValidationError(f"Invalid kurta style: '{iw.kurta_style}'")
            if iw.saree_drape_style and iw.saree_drape_style not in self.registry.indian_wear.get("saree_drape_styles", {}):
                raise TaxonomyValidationError(f"Invalid saree drape style: '{iw.saree_drape_style}'")

        # Footwear extension
        if classification.footwear:
            if root != "footwear":
                raise TaxonomyValidationError(
                    f"Footwear attributes cannot be attached to non-footwear category '{classification.category_id}'"
                )
            fw = classification.footwear
            if fw.footwear_type and fw.footwear_type not in self.registry.footwear.get("footwear_types", []):
                raise TaxonomyValidationError(f"Invalid footwear type: '{fw.footwear_type}'")
            if fw.closure_type and fw.closure_type not in self.registry.footwear.get("closure_types", []):
                raise TaxonomyValidationError(f"Invalid footwear closure type: '{fw.closure_type}'")

        # Accessories extension
        if classification.accessories:
            if root != "accessories":
                raise TaxonomyValidationError(
                    f"Accessory attributes cannot be attached to non-accessory category '{classification.category_id}'"
                )
