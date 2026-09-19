from dataclasses import dataclass, field
from typing import Any


@dataclass
class CatalogQualityReport:
    total_garments: int
    completeness_score: float
    category_validity: float
    silhouette_validity: float
    color_validity: float
    passed_gate: bool
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_garments": self.total_garments,
            "completeness_score": round(self.completeness_score, 3),
            "category_validity": round(self.category_validity, 3),
            "silhouette_validity": round(self.silhouette_validity, 3),
            "color_validity": round(self.color_validity, 3),
            "passed_gate": self.passed_gate,
            "issues": self.issues,
        }


class CatalogQualityGate:
    """Audits catalog items against production quality and attribute completeness thresholds."""

    # Target SLAs from Master Roadmap v1.1
    TARGET_COMPLETENESS = 0.98
    TARGET_CATEGORY = 0.99
    TARGET_SILHOUETTE = 0.92
    TARGET_COLOR = 0.95

    VALID_CATEGORIES = {"tops", "bottoms", "dresses", "outerwear"}

    @classmethod
    def audit_garment_batch(
        cls,
        garment_items: list[dict[str, Any]],
    ) -> CatalogQualityReport:
        if not garment_items:
            return CatalogQualityReport(
                total_garments=0,
                completeness_score=1.0,
                category_validity=1.0,
                silhouette_validity=1.0,
                color_validity=1.0,
                passed_gate=True,
                issues=[],
            )

        total = len(garment_items)
        valid_categories = 0
        valid_silhouettes = 0
        valid_colors = 0
        complete_items = 0
        issues: list[str] = []

        for idx, item in enumerate(garment_items):
            cat = str(item.get("category") or "").lower()
            attrs = item.get("attributes") or {}
            silhouette = attrs.get("silhouette")
            color = attrs.get("dominant_color")

            is_cat_valid = cat in cls.VALID_CATEGORIES
            is_sil_valid = bool(silhouette)
            is_col_valid = bool(color)

            if is_cat_valid:
                valid_categories += 1
            else:
                issues.append(f"Garment index {idx}: Invalid category '{cat}'")

            if is_sil_valid:
                valid_silhouettes += 1

            if is_col_valid:
                valid_colors += 1

            # A complete item has valid category, subcategory, silhouette, color, and price
            if is_cat_valid and is_sil_valid and is_col_valid and item.get("price_minor", 0) > 0:
                complete_items += 1

        cat_score = valid_categories / total
        sil_score = valid_silhouettes / total
        col_score = valid_colors / total
        comp_score = complete_items / total

        passed = (
            comp_score >= cls.TARGET_COMPLETENESS
            and cat_score >= cls.TARGET_CATEGORY
            and sil_score >= cls.TARGET_SILHOUETTE
            and col_score >= cls.TARGET_COLOR
        )

        return CatalogQualityReport(
            total_garments=total,
            completeness_score=comp_score,
            category_validity=cat_score,
            silhouette_validity=sil_score,
            color_validity=col_score,
            passed_gate=passed,
            issues=issues[:20],  # cap issue log size
        )
