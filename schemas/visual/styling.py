"""FashXStudio Outfit, Styling & Fashion Experience System Contracts — Phase 10.

Defines Pydantic v2 data contracts for Styling, Outfit Building, Look Composition,
Mix & Match, Preferences, Saved Looks, and Commerce Integration (Sections 10.1 - 10.88):
- Screen Inventory: ST01-ST09 Styling Screens
- Core Objects: Style, Look, Outfit, OutfitSlot, OutfitItem, Recommendation, StylePreference, SavedLook
- Builder State Machine: Empty, Loading, Editing, Saving, Saved, Unsaved Changes, Preview, Error
- Slot Model: Configurable slots (Top, Bottom, Footwear, Outerwear, Accessory, Bag)
- Mix & Match: Candidate items per slot with instant swap capability
- Commerce Integration: Authoritative availability validation and cart handoff

All schemas enforce extra="forbid" via BaseContractModel (Constitution Rule I02).
"""

from enum import StrEnum
from typing import Any
from pydantic import Field
from schemas.base import BaseContractModel
from schemas.visual.fashion import VisualContentModel


# ---------------------------------------------------------------------------
# Enums (Sections 10.2, 10.11, 10.36, 10.37)
# ---------------------------------------------------------------------------

class StylingScreenId(StrEnum):
    """Screen identifiers for Styling & Outfit Experience ecosystem (Section 10.2)."""
    ST01_STYLE_HOME = "ST01"
    ST02_OUTFIT_BUILDER = "ST02"
    ST03_LOOK_BUILDER = "ST03"
    ST04_MIX_MATCH = "ST04"
    ST05_STYLE_RECOMMENDATION = "ST05"
    ST06_OUTFIT_PREVIEW = "ST06"
    ST07_OUTFIT_DETAIL = "ST07"
    ST08_SAVED_LOOKS = "ST08"
    ST09_STYLE_PREFERENCES = "ST09"


class SlotCategory(StrEnum):
    """Configurable outfit category slots (Section 10.11)."""
    TOP = "top"
    BOTTOM = "bottom"
    FOOTWEAR = "footwear"
    OUTERWEAR = "outerwear"
    ACCESSORY = "accessory"
    BAG = "bag"


class SlotState(StrEnum):
    """Individual slot state inside the builder canvas (Section 10.11, 10.12)."""
    EMPTY = "empty"
    FILLED = "filled"
    ACTIVE = "active"
    LOCKED = "locked"
    DISABLED = "disabled"


class BuilderState(StrEnum):
    """Unified builder state machine (Section 10.36, 10.37)."""
    EMPTY = "empty"
    LOADING = "loading"
    EDITING = "editing"
    SAVING = "saving"
    SAVED = "saved"
    UNSAVED_CHANGES = "unsaved_changes"
    PREVIEW = "preview"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


class OutfitSource(StrEnum):
    """Origin of the outfit composition (Section 10.22, 10.47, 10.48)."""
    MANUAL = "manual"
    AI_GENERATED = "ai_generated"
    EDITORIAL = "editorial"
    COMMUNITY = "community"


# ---------------------------------------------------------------------------
# Core Outfit & Slot Models (Sections 10.10 - 10.15, 10.61, 10.62)
# ---------------------------------------------------------------------------

class OutfitItemContract(BaseContractModel):
    """Single item occupying an outfit slot, tied to catalog product (Section 10.62)."""
    slot_id: str
    product_id: str
    title: str
    brand: str
    image_uri: str
    price: float = Field(ge=0.0)
    original_price: float | None = Field(default=None, ge=0.0)
    selected_variants: dict[str, str] = Field(default_factory=dict)
    is_available: bool = Field(default=True)
    quantity: int = Field(default=1, ge=1, le=10)


class OutfitSlotContract(BaseContractModel):
    """Configurable slot specification within the builder canvas (Section 10.11)."""
    id: str
    category: SlotCategory
    name: str
    position: int = Field(ge=0)
    required: bool = Field(default=True)
    item: OutfitItemContract | None = Field(default=None)
    state: SlotState = Field(default=SlotState.EMPTY)


class OutfitContract(BaseContractModel):
    """Complete wearable outfit model (Section 10.4, 10.61)."""
    id: str
    name: str
    style_id: str
    style_name: str
    slots: list[OutfitSlotContract] = Field(default_factory=list)
    hero_image_uri: str | None = Field(default=None)
    source: OutfitSource = Field(default=OutfitSource.MANUAL)
    total_price: float = Field(default=0.0, ge=0.0)
    is_complete: bool = Field(default=False)
    notes: str | None = Field(default=None)


# ---------------------------------------------------------------------------
# Mix & Match & Recommendations (Sections 10.16, 10.17, 10.20 - 10.22)
# ---------------------------------------------------------------------------

class CandidateItemContract(BaseContractModel):
    """Alternative candidate products for rapid slot swapping (Section 10.16)."""
    slot_id: str
    category: SlotCategory
    products: list[OutfitItemContract] = Field(default_factory=list)


class MixMatchContract(BaseContractModel):
    """Mix & Match experiment matrix (Section 10.16, 10.17)."""
    outfit_id: str
    current_items: list[OutfitItemContract] = Field(default_factory=list)
    candidates_by_slot: list[CandidateItemContract] = Field(default_factory=list)


class StylePreferenceContract(BaseContractModel):
    """User aesthetic preference settings (Section 10.33, 10.34)."""
    user_id: str
    preferred_styles: list[str] = Field(default_factory=list)
    preferred_fits: list[str] = Field(default_factory=list)
    preferred_colors: list[str] = Field(default_factory=list)
    preferred_materials: list[str] = Field(default_factory=list)
    budget_tier: str = Field(default="medium")


class SavedLookContract(BaseContractModel):
    """Persisted user outfit or look (Section 10.29 - 10.32)."""
    id: str
    user_id: str
    name: str
    style_name: str
    created_at: str
    updated_at: str
    items: list[OutfitItemContract] = Field(default_factory=list)
    hero_image_uri: str | None = Field(default=None)
    is_favorite: bool = Field(default=False)
    collection_tag: str | None = Field(default=None)


# ---------------------------------------------------------------------------
# Action Requests & Validation (Sections 10.13 - 10.15, 10.27, 10.28, 10.31)
# ---------------------------------------------------------------------------

class AddSlotItemRequestContract(BaseContractModel):
    """Payload to add a product into a specific outfit slot."""
    slot_id: str
    product_id: str
    selected_variants: dict[str, str] = Field(default_factory=dict)


class ReplaceSlotItemRequestContract(BaseContractModel):
    """Payload to swap an existing item in a slot."""
    slot_id: str
    new_product_id: str
    selected_variants: dict[str, str] = Field(default_factory=dict)


class SaveOutfitRequestContract(BaseContractModel):
    """Payload to persist an outfit as a saved look."""
    outfit_id: str
    name: str
    user_id: str = Field(default="user-1")
    collection_tag: str | None = Field(default=None)


class ShopOutfitAvailabilityContract(BaseContractModel):
    """Pre-purchase validation result before transferring outfit to cart (Section 10.28)."""
    outfit_id: str
    total_items: int = Field(ge=0)
    available_items: int = Field(ge=0)
    available_product_ids: list[str] = Field(default_factory=list)
    unavailable_product_ids: list[str] = Field(default_factory=list)
    can_proceed_to_cart: bool = Field(default=True)
    total_price: float = Field(default=0.0, ge=0.0)


# ---------------------------------------------------------------------------
# Screen Templates (ST01 – ST09, Section 10.2, 10.59)
# ---------------------------------------------------------------------------

class StyleHomeTemplateSpecContract(BaseContractModel):
    """ST01: Style Home entry point specification (Section 10.5, 10.6)."""
    screen_id: StylingScreenId = Field(default=StylingScreenId.ST01_STYLE_HOME)
    featured_style: VisualContentModel
    popular_styles: list[VisualContentModel] = Field(default_factory=list)
    recommended_looks: list[VisualContentModel] = Field(default_factory=list)
    saved_looks_preview: list[SavedLookContract] = Field(default_factory=list)


class OutfitBuilderTemplateSpecContract(BaseContractModel):
    """ST02: Primary interactive outfit workspace specification (Section 10.7 - 10.10)."""
    screen_id: StylingScreenId = Field(default=StylingScreenId.ST02_OUTFIT_BUILDER)
    outfit: OutfitContract
    active_slot_id: str | None = Field(default=None)
    available_categories: list[SlotCategory] = Field(default_factory=list)
    state: BuilderState = Field(default=BuilderState.EDITING)


class LookBuilderTemplateSpecContract(BaseContractModel):
    """ST03: Creative visual/editorial look composition canvas (Section 10.18, 10.19)."""
    screen_id: StylingScreenId = Field(default=StylingScreenId.ST03_LOOK_BUILDER)
    look_id: str
    title: str
    style_tags: list[str] = Field(default_factory=list)
    context_narrative: str
    visual_items: list[OutfitItemContract] = Field(default_factory=list)
    state: BuilderState = Field(default=BuilderState.EDITING)


class MixMatchTemplateSpecContract(BaseContractModel):
    """ST04: Rapid outfit alternative experimentation matrix (Section 10.16, 10.17)."""
    screen_id: StylingScreenId = Field(default=StylingScreenId.ST04_MIX_MATCH)
    matrix: MixMatchContract


class StyleRecommendationTemplateSpecContract(BaseContractModel):
    """ST05: Explainable style recommendations with trust boundary (Section 10.20 - 10.22)."""
    screen_id: StylingScreenId = Field(default=StylingScreenId.ST05_STYLE_RECOMMENDATION)
    recommended_style_name: str
    explanation: str
    recommended_looks: list[VisualContentModel] = Field(default_factory=list)
    recommended_products: list[VisualContentModel] = Field(default_factory=list)


class OutfitPreviewTemplateSpecContract(BaseContractModel):
    """ST06: Clean read-only outfit composition preview (Section 10.23, 10.24)."""
    screen_id: StylingScreenId = Field(default=StylingScreenId.ST06_OUTFIT_PREVIEW)
    outfit: OutfitContract
    item_count: int = Field(ge=0)
    total_price: float = Field(ge=0.0)


class OutfitDetailTemplateSpecContract(BaseContractModel):
    """ST07: Comprehensive outfit detail with shoppable pieces (Section 10.25 - 10.28)."""
    screen_id: StylingScreenId = Field(default=StylingScreenId.ST07_OUTFIT_DETAIL)
    outfit: OutfitContract
    constituent_items: list[OutfitItemContract] = Field(default_factory=list)
    similar_outfits: list[OutfitContract] = Field(default_factory=list)
    availability: ShopOutfitAvailabilityContract


class SavedLooksTemplateSpecContract(BaseContractModel):
    """ST08: User saved looks archive and collection manager (Section 10.29 - 10.32)."""
    screen_id: StylingScreenId = Field(default=StylingScreenId.ST08_SAVED_LOOKS)
    saved_looks: list[SavedLookContract] = Field(default_factory=list)
    total_saved: int = Field(default=0, ge=0)
    active_filter: str = Field(default="all")


class StylePreferencesTemplateSpecContract(BaseContractModel):
    """ST09: User style preference selector specification (Section 10.33 - 10.35)."""
    screen_id: StylingScreenId = Field(default=StylingScreenId.ST09_STYLE_PREFERENCES)
    preferences: StylePreferenceContract
    available_styles: list[str] = Field(default_factory=list)
    available_fits: list[str] = Field(default_factory=list)
    available_colors: list[str] = Field(default_factory=list)
    available_materials: list[str] = Field(default_factory=list)
