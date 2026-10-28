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
    eligible_items: int = 0
    eligibility_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_garments": self.total_garments,
            "completeness_score": round(self.completeness_score, 3),
            "category_validity": round(self.category_validity, 3),
            "silhouette_validity": round(self.silhouette_validity, 3),
            "color_validity": round(self.color_validity, 3),
            "passed_gate": self.passed_gate,
            "eligible_items": self.eligible_items,
            "eligibility_rate": round(self.eligibility_rate, 3),
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
    VALID_SILHOUETTES = {
        "slim",
        "regular",
        "relaxed",
        "oversized",
        "fitted",
        "straight",
        "a-line",
        "flared",
        "skinny",
        "wide-leg",
        "tailored",
    }
    VALID_COLORS = {
        "black",
        "white",
        "grey",
        "gray",
        "beige",
        "brown",
        "red",
        "maroon",
        "orange",
        "yellow",
        "green",
        "olive",
        "teal",
        "blue",
        "navy",
        "purple",
        "pink",
        "multi",
        "cream",
        "charcoal",
        "sage",
        "terracotta",
        "indigo",
    }
    VALID_RIGHTS = {"owned", "licensed", "partner_authorized"}

    @classmethod
    def is_item_eligible(cls, item: dict[str, Any]) -> tuple[bool, list[str]]:
        """Audit an individual catalog item for feed eligibility.

        Prevents batch averages from masking individual invalid records.
        """
        reasons: list[str] = []
        cat = str(item.get("category") or "").strip().lower()
        if cat not in cls.VALID_CATEGORIES:
            reasons.append(f"Invalid category '{cat}'")

        price = item.get("price_minor", 0)
        if not isinstance(price, int) or price <= 0:
            reasons.append(f"Invalid price_minor {price} (must be > 0)")

        # Offer stock check
        if item.get("in_stock") is False:
            reasons.append("Item is out of stock")

        # Source clearance check (if provided in record)
        source_status = item.get("source_status")
        if source_status is not None and source_status != "cleared":
            reasons.append(f"Source status '{source_status}' is not cleared")

        # Image check (if provided in record)
        image_url = item.get("image_url")
        if image_url is not None:
            if not isinstance(image_url, str) or not (
                image_url.startswith("https://") or image_url.startswith("http://")
            ):
                reasons.append("Invalid or missing image URL")

        image_rights = item.get("image_rights")
        if image_rights is not None and image_rights.lower() not in cls.VALID_RIGHTS:
            reasons.append(f"Invalid image rights '{image_rights}'")

        return len(reasons) == 0, reasons

    @classmethod
    def audit_garment_batch(
        cls,
        garment_items: list[dict[str, Any]],
    ) -> CatalogQualityReport:
        # Hardening: An empty batch fails closed and cannot pass as production-ready
        if not garment_items:
            return CatalogQualityReport(
                total_garments=0,
                completeness_score=0.0,
                category_validity=0.0,
                silhouette_validity=0.0,
                color_validity=0.0,
                passed_gate=False,
                eligible_items=0,
                eligibility_rate=0.0,
                issues=["Empty catalog batch cannot pass production quality gate"],
            )

        total = len(garment_items)
        valid_categories = 0
        valid_silhouettes = 0
        valid_colors = 0
        complete_items = 0
        eligible_items = 0
        issues: list[str] = []

        for idx, item in enumerate(garment_items):
            cat = str(item.get("category") or "").strip().lower()
            attrs = item.get("attributes") or {}
            silhouette = str(attrs.get("silhouette") or "").strip().lower()
            color = str(attrs.get("dominant_color") or "").strip().lower()

            is_cat_valid = cat in cls.VALID_CATEGORIES
            is_sil_valid = bool(silhouette) and (silhouette in cls.VALID_SILHOUETTES or len(silhouette) > 2)
            is_col_valid = bool(color) and (color in cls.VALID_COLORS or len(color) > 2)

            if is_cat_valid:
                valid_categories += 1
            else:
                issues.append(f"Garment index {idx}: Invalid category '{cat}'")

            if is_sil_valid:
                valid_silhouettes += 1
            else:
                issues.append(f"Garment index {idx}: Invalid silhouette '{silhouette}'")

            if is_col_valid:
                valid_colors += 1
            else:
                issues.append(f"Garment index {idx}: Invalid dominant color '{color}'")

            # A complete item has valid category, silhouette, color, and price > 0
            if is_cat_valid and is_sil_valid and is_col_valid and item.get("price_minor", 0) > 0:
                complete_items += 1

            # Individual eligibility check
            eligible, item_issues = cls.is_item_eligible(item)
            if eligible:
                eligible_items += 1
            else:
                for r in item_issues:
                    issues.append(f"Garment index {idx}: {r}")

        cat_score = valid_categories / total
        sil_score = valid_silhouettes / total
        col_score = valid_colors / total
        comp_score = complete_items / total
        eligibility_rate = eligible_items / total

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
            eligible_items=eligible_items,
            eligibility_rate=eligibility_rate,
            issues=issues[:20],  # cap issue log size
        )
