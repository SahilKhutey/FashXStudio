from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class CandidateItem:
    garment_id: UUID
    category: str
    subcategory: str | None
    price_minor: int
    in_stock: bool
    dominant_color: str | None = None
    silhouette: str | None = None
    formality: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None


@dataclass
class FilterCriteria:
    budget_min: int | None = None
    budget_max: int | None = None
    allowed_categories: list[str] | None = None
    avoided_colors: list[str] = field(default_factory=list)
    excluded_garment_ids: set[UUID] = field(default_factory=set)


class DeterministicFilter:
    """Stage 1: Enforces deterministic constraints before ranking (stock, budget, exclusions, avoided colors)."""

    @classmethod
    def filter_candidate(
        cls, item: CandidateItem, criteria: FilterCriteria
    ) -> tuple[bool, str | None]:
        # 1. Stock check
        if not item.in_stock:
            return False, "Item is currently out of stock"

        # 2. Excluded items check (Rule I06 / Feed Exclusions)
        if item.garment_id in criteria.excluded_garment_ids:
            return False, "Item previously excluded or disliked by user"

        # 3. Budget ceiling
        if criteria.budget_max is not None and item.price_minor > criteria.budget_max:
            return False, f"Price {item.price_minor} exceeds budget ceiling {criteria.budget_max}"

        # 4. Budget floor (if specified)
        if criteria.budget_min is not None and item.price_minor < criteria.budget_min:
            return False, f"Price {item.price_minor} below minimum budget {criteria.budget_min}"

        # 5. Category preference filtering (if specified)
        if criteria.allowed_categories and item.category not in criteria.allowed_categories:
            return False, f"Category '{item.category}' not in preferred categories"

        # 6. Hard-avoided colors
        if item.dominant_color:
            avoided_lower = {c.lower() for c in criteria.avoided_colors}
            if item.dominant_color.lower() in avoided_lower:
                return (
                    False,
                    f"Dominant color '{item.dominant_color}' is explicitly avoided by user",
                )

        return True, None

    @classmethod
    def filter_candidates(
        cls, items: list[CandidateItem], criteria: FilterCriteria
    ) -> list[CandidateItem]:
        """Apply deterministic filters to a candidate pool."""
        return [item for item in items if cls.filter_candidate(item, criteria)[0]]
