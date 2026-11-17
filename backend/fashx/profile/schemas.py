from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SizeSystem(str, Enum):
    IN = "IN"
    US = "US"
    UK = "UK"
    EU = "EU"
    INTL = "INTL"


class PreferredFit(str, Enum):
    SLIM = "SLIM"
    REGULAR = "REGULAR"
    RELAXED = "RELAXED"
    OVERSIZED = "OVERSIZED"
    NO_PREFERENCE = "NO_PREFERENCE"


class StylePreference(str, Enum):
    CASUAL = "CASUAL"
    FORMAL = "FORMAL"
    SMART_CASUAL = "SMART_CASUAL"
    MINIMAL = "MINIMAL"
    STREETWEAR = "STREETWEAR"
    SPORTSWEAR = "SPORTSWEAR"
    ETHNIC = "ETHNIC"
    TRADITIONAL = "TRADITIONAL"
    FUSION = "FUSION"
    PARTY = "PARTY"
    NO_PREFERENCE = "NO_PREFERENCE"


class ColorPreference(str, Enum):
    BLACK = "BLACK"
    WHITE = "WHITE"
    GREY = "GREY"
    NAVY = "NAVY"
    BLUE = "BLUE"
    RED = "RED"
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    PINK = "PINK"
    PURPLE = "PURPLE"
    BROWN = "BROWN"
    BEIGE = "BEIGE"
    MAROON = "MAROON"
    MULTICOLOR = "MULTICOLOR"
    NO_PREFERENCE = "NO_PREFERENCE"


class ProductCategory(str, Enum):
    TOPS = "TOPS"
    SHIRTS = "SHIRTS"
    T_SHIRTS = "T_SHIRTS"
    BOTTOMS = "BOTTOMS"
    JEANS = "JEANS"
    TROUSERS = "TROUSERS"
    DRESSES = "DRESSES"
    KURTAS = "KURTAS"
    ETHNIC_WEAR = "ETHNIC_WEAR"
    FOOTWEAR = "FOOTWEAR"
    ACCESSORIES = "ACCESSORIES"


class ShoppingIntent(str, Enum):
    EVERYDAY_WEAR = "EVERYDAY_WEAR"
    WORKWEAR = "WORKWEAR"
    COLLEGE_WEAR = "COLLEGE_WEAR"
    OCCASION_WEAR = "OCCASION_WEAR"
    FESTIVE_WEAR = "FESTIVE_WEAR"
    SPORTSWEAR = "SPORTSWEAR"
    TRAVEL_WEAR = "TRAVEL_WEAR"


class ShoppingBudget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    currency: str = Field(default="INR", min_length=3, max_length=3)
    min: Decimal | None = Field(default=None, ge=0)
    max: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_budget_range(self) -> ShoppingBudget:
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("Minimum budget cannot be greater than maximum budget")
        return self


class ShoppingPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget: ShoppingBudget | None = None
    shopping_intents: list[ShoppingIntent] = Field(default_factory=list)
    preferred_brands: list[str] = Field(default_factory=list)
    avoid_materials: list[str] = Field(default_factory=list)
    sustainability_preference: str | None = Field(default="NO_PREFERENCE", max_length=64)


class CategorySizeItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_code: str = Field(min_length=1, max_length=64)
    size_system: SizeSystem
    size_label: str = Field(min_length=1, max_length=32)


class CategorySizesUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sizes: list[CategorySizeItem]


class ShopperProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    height_cm: Decimal | None = Field(default=None, ge=80, le=250)
    weight_kg: Decimal | None = Field(default=None, ge=20, le=400)
    preferred_size_system: SizeSystem | None = None
    preferred_fit: PreferredFit | None = None
    style_preferences: list[StylePreference] = Field(default_factory=list)
    preferred_colors: list[ColorPreference] = Field(default_factory=list)
    product_categories: list[ProductCategory] = Field(default_factory=list)
    shopping_preferences: ShoppingPreferences = Field(default_factory=ShoppingPreferences)
    category_sizes: list[CategorySizeItem] = Field(default_factory=list)


ProfileCreate = ShopperProfileCreate


class ShopperProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    height_cm: Decimal | None = Field(default=None, ge=80, le=250)
    weight_kg: Decimal | None = Field(default=None, ge=20, le=400)
    preferred_size_system: SizeSystem | None = None
    preferred_fit: PreferredFit | None = None
    style_preferences: list[StylePreference] | None = None
    preferred_colors: list[ColorPreference] | None = None
    product_categories: list[ProductCategory] | None = None
    shopping_preferences: ShoppingPreferences | None = None
    category_sizes: list[CategorySizeItem] | None = None
    expected_version: int | None = Field(default=None, ge=1)


ProfileUpdate = ShopperProfileUpdate


class ShopperProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    height_cm: float | None = None
    weight_kg: float | None = None
    preferred_size_system: str | None = None
    preferred_fit: str | None = None
    style_preferences: list[str] = Field(default_factory=list)
    preferred_colors: list[str] = Field(default_factory=list)
    product_categories: list[str] = Field(default_factory=list)
    shopping_preferences: dict[str, Any] = Field(default_factory=dict)
    category_sizes: list[CategorySizeItem] = Field(default_factory=list)
    version: int
    created_at: datetime
    updated_at: datetime
    build: str | None = None
    consents: dict[str, bool] = Field(default_factory=dict)


ProfileResponse = ShopperProfileResponse


class FeatureReadiness(BaseModel):
    ready: bool
    missing_fields: list[str] = Field(default_factory=list)


class FeatureCompletenessResponse(BaseModel):
    overall_status: str
    overall_percentage: int = 0
    features: dict[str, FeatureReadiness]
