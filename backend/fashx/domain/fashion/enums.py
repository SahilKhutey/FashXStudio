from __future__ import annotations

from enum import StrEnum


class TaxonomyType(StrEnum):
    CATEGORY = "category"
    SUBCATEGORY = "subcategory"
    GARMENT = "garment"
    STYLE = "style"
    FIT = "fit"
    MATERIAL = "material"
    COLOR = "color"
    PATTERN = "pattern"
    OCCASION = "occasion"
    SEASON = "season"
    AUDIENCE = "audience"


class TaxonomyStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ClassificationSource(StrEnum):
    MANUAL = "manual"
    IMPORTED = "imported"
    RULE = "rule"
    AI = "ai"
