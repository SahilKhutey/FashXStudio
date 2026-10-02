"""Visual Design — Phase 13: Profile, Personalization & Saved Experience System Schemas.

Establishes strict Pydantic v2 data contracts enforcing extra="forbid" via BaseContractModel.
Defines specifications for PR01 - PR11, user identity, explicit vs inferred preferences,
activity tracking, saved items (products, looks, fashion, collections), shopping wishlist,
recommendation tuning, regional context, and account controls (Sections 13.1 - 13.103).
"""

from enum import StrEnum
from typing import Any
from pydantic import Field
from schemas.base import BaseContractModel


# ---------------------------------------------------------------------------
# Enums & Taxonomies (Sections 13.2, 13.4, 13.17, 13.24, 13.40, 13.65)
# ---------------------------------------------------------------------------

class PersonalScreenId(StrEnum):
    """Authoritative screen identifiers for Phase 13 Personal space (Section 13.2)."""
    PR01_PROFILE = "PR01"
    PR02_PERSONAL_DASHBOARD = "PR02"
    PR03_SAVED_PRODUCTS = "PR03"
    PR04_SAVED_LOOKS = "PR04"
    PR05_SAVED_FASHION = "PR05"
    PR06_WISHLIST = "PR06"
    PR07_RECENTLY_VIEWED = "PR07"
    PR08_PREFERENCES = "PR08"
    PR09_RECOMMENDATION_PREFERENCES = "PR09"
    PR10_REGIONAL_PREFERENCES = "PR10"
    PR11_ACCOUNT_SETTINGS = "PR11"


class PersonalState(StrEnum):
    """Operational lifecycle state of personal space interfaces (Section 13.2)."""
    LOADING = "loading"
    LOADED = "loaded"
    EMPTY = "empty"
    PARTIAL = "partial"
    ERROR = "error"
    SAVING = "saving"
    SAVED = "saved"
    UNSAVED_CHANGES = "unsaved_changes"
    RESTRICTED = "restricted"
    SESSION_EXPIRED = "session_expired"


class ActivityEntityType(StrEnum):
    """Classification of interacted items in user history (Section 13.22, 13.24)."""
    PRODUCT = "product"
    LOOK = "look"
    FASHION = "fashion"
    TREND = "trend"
    COLLECTION = "collection"


class ActivityAction(StrEnum):
    """Interaction verb performed by user (Section 13.24)."""
    VIEW = "view"
    SEARCH = "search"
    SAVE = "save"
    UNSAVE = "unsave"
    OPEN = "open"
    EDIT = "edit"
    SHOP = "shop"


class SavedFashionContentType(StrEnum):
    """Fashion content taxonomy for saved items (Section 13.17, 13.18)."""
    STORY = "story"
    ARTICLE = "article"
    COLLECTION = "collection"
    EDITORIAL = "editorial"
    TREND = "trend"
    BRAND = "brand"


class SavedItemType(StrEnum):
    """Target category for save/bookmark mutations (Section 13.12)."""
    PRODUCT = "product"
    LOOK = "look"
    FASHION = "fashion"
    WISHLIST = "wishlist"


# ---------------------------------------------------------------------------
# Core Activity & Saved Domain Models (Sections 13.12 - 13.25)
# ---------------------------------------------------------------------------

class ActivityContract(BaseContractModel):
    """Logged interaction event preserving user history without assuming endorsement (Section 13.23, 13.24)."""
    entity_id: str
    entity_type: ActivityEntityType
    action: ActivityAction
    title: str
    subtitle: str | None = Field(default=None)
    image_url: str | None = Field(default=None)
    timestamp: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SavedProductContract(BaseContractModel):
    """Saved product representation communicating state via text and badge (Section 13.13, 13.14, 13.74)."""
    id: str
    product_id: str
    brand: str
    name: str
    price: float
    currency: str = Field(default="USD")
    image_url: str | None = Field(default=None)
    is_saved: bool = Field(default=True)
    saved_state_label: str = Field(default="Saved in Products")
    availability: str = Field(default="in_stock")  # "in_stock", "low_stock", "out_of_stock"
    saved_at: str


class SavedLookContract(BaseContractModel):
    """Saved outfit composition supporting styling and editing workflows (Section 13.15, 13.16)."""
    id: str
    look_id: str
    title: str
    style: str
    image_url: str | None = Field(default=None)
    collection_id: str | None = Field(default=None)
    items_count: int = Field(default=3)
    supported_actions: list[str] = Field(
        default_factory=lambda: ["open", "edit", "duplicate", "share", "shop", "remove"]
    )
    saved_at: str


class SavedFashionContract(BaseContractModel):
    """Editorial, brand, trend, or story content bookmarked by user (Section 13.17, 13.18)."""
    id: str
    content_id: str
    content_type: SavedFashionContentType
    title: str
    author_or_brand: str | None = Field(default=None)
    image_url: str | None = Field(default=None)
    saved_at: str


class WishlistItemContract(BaseContractModel):
    """Shopping-intent item tracking real-time commerce availability and changes (Section 13.19 - 13.21)."""
    id: str
    product_id: str
    brand: str
    name: str
    price: float
    currency: str = Field(default="USD")
    image_url: str | None = Field(default=None)
    availability: str = Field(default="in_stock")  # "in_stock", "out_of_stock", "discontinued"
    is_available: bool = Field(default=True)
    availability_notice: str | None = Field(default=None)
    alternative_product_id: str | None = Field(default=None)
    added_at: str


class PersonalCollectionContract(BaseContractModel):
    """User-created grouping for organizing saved looks and fashion (Section 13.66, 13.67)."""
    id: str
    name: str
    description: str | None = Field(default=None)
    item_count: int = Field(default=0)
    cover_image_url: str | None = Field(default=None)
    created_at: str


# ---------------------------------------------------------------------------
# Preference & Identity Models (Sections 13.4, 13.5, 13.26 - 13.38)
# ---------------------------------------------------------------------------

class ExplicitPreferencesContract(BaseContractModel):
    """User-chosen preferences that can be explicitly toggled and saved (Section 13.4, 13.27, 13.28)."""
    styles: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    colors: list[str] = Field(default_factory=list)
    fits: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    contexts: list[str] = Field(default_factory=list)


class InferredPreferencesContract(BaseContractModel):
    """System-observed behavior strictly separated from explicit choices (Section 13.4, 13.5)."""
    frequently_viewed_styles: list[str] = Field(default_factory=list)
    frequently_viewed_categories: list[str] = Field(default_factory=list)
    frequently_viewed_colors: list[str] = Field(default_factory=list)
    observation_notice: str = Field(
        default="Inferred from browsing history. Does not alter your explicit style choices."
    )


class SavedSummaryContract(BaseContractModel):
    """Aggregate tally of all saved assets for quick preview (Section 13.6, 13.7)."""
    products_count: int = Field(default=0)
    looks_count: int = Field(default=0)
    fashion_count: int = Field(default=0)
    wishlist_count: int = Field(default=0)
    collections_count: int = Field(default=0)


class RecommendationPreferencesContract(BaseContractModel):
    """Controls and transparency for algorithmic suggestions (Section 13.29 - 13.31)."""
    personalized_recommendations: bool = Field(default=True)
    use_style_preferences: bool = Field(default=True)
    use_regional_context: bool = Field(default=True)
    transparency_signals: list[str] = Field(
        default_factory=lambda: ["selected_styles", "saved_items", "recent_activity"]
    )


class RegionalPreferencesContract(BaseContractModel):
    """Geographic fashion context decoupled from physical device GPS location (Section 13.34 - 13.36)."""
    preferred_country: str = Field(default="France")
    preferred_state: str | None = Field(default="Île-de-France")
    preferred_city: str | None = Field(default="Paris")
    regional_discovery_enabled: bool = Field(default=True)
    delivery_region: str = Field(default="Europe - Western")
    disclaimer: str = Field(
        default="Preferred region is a discovery preference, not current device GPS location."
    )


class PersonalAIPreferencesContract(BaseContractModel):
    """AI feature tuning and boundaries for personal context (Section 13.37, 13.38, 13.89)."""
    ai_recommendations_enabled: bool = Field(default=True)
    ai_personalization_enabled: bool = Field(default=True)
    ai_interaction_mode: str = Field(default="propose_and_assist")
    ai_context_permitted: list[str] = Field(
        default_factory=lambda: ["selected_styles", "saved_looks"]
    )


class AccountSettingsContract(BaseContractModel):
    """Account management, security, and notification settings (Section 13.39 - 13.41)."""
    user_id: str = Field(default="usr_fashx_01")
    email: str = Field(default="alexandra.chen@example.com")
    display_name: str = Field(default="Alexandra Chen")
    notifications_enabled: bool = Field(default=True)
    privacy_level: str = Field(default="standard")  # "minimal", "standard", "enhanced"
    two_factor_auth: bool = Field(default=True)
    activity_history_retention: str = Field(default="90_days")
    categories: list[str] = Field(
        default_factory=lambda: ["profile", "account", "notifications", "privacy", "security", "personalization"]
    )


# ---------------------------------------------------------------------------
# Template Specifications: PR01 - PR11 (Section 13.2, 13.6 - 13.49)
# ---------------------------------------------------------------------------

class ProfileTemplateSpecContract(BaseContractModel):
    """PR01: Main personal profile screen specification (Section 13.6 - 13.8)."""
    screen_id: PersonalScreenId = Field(default=PersonalScreenId.PR01_PROFILE)
    user_id: str
    display_name: str
    avatar_url: str | None = Field(default=None)
    bio: str | None = Field(default=None)
    style_tags: list[str] = Field(default_factory=list)
    saved_summary: SavedSummaryContract
    preferences_preview: list[str] = Field(default_factory=list)
    recent_activity_preview: list[ActivityContract] = Field(default_factory=list)
    regional_context: RegionalPreferencesContract
    state: PersonalState = Field(default=PersonalState.LOADED)


class PersonalDashboardTemplateSpecContract(BaseContractModel):
    """PR02: Personalized dashboard home prioritizing Continue -> Saved -> Recommendations (Section 13.9 - 13.11)."""
    screen_id: PersonalScreenId = Field(default=PersonalScreenId.PR02_PERSONAL_DASHBOARD)
    welcome_title: str
    continue_exploring: list[dict[str, Any]] = Field(default_factory=list)
    recommended_products: list[SavedProductContract] = Field(default_factory=list)
    recommended_looks: list[SavedLookContract] = Field(default_factory=list)
    saved_preview: list[dict[str, Any]] = Field(default_factory=list)
    recently_viewed: list[ActivityContract] = Field(default_factory=list)
    regional_highlights: list[dict[str, Any]] = Field(default_factory=list)
    ai_suggestions: list[dict[str, Any]] = Field(default_factory=list)
    module_states: dict[str, PersonalState] = Field(default_factory=dict)
    state: PersonalState = Field(default=PersonalState.LOADED)


class SavedProductsTemplateSpecContract(BaseContractModel):
    """PR03: Saved products catalog with filter and sort controls (Section 13.13, 13.14)."""
    screen_id: PersonalScreenId = Field(default=PersonalScreenId.PR03_SAVED_PRODUCTS)
    title: str = Field(default="Saved Products")
    total_count: int
    items: list[SavedProductContract] = Field(default_factory=list)
    active_filter: str | None = Field(default=None)
    active_sort: str = Field(default="recently_saved")
    state: PersonalState = Field(default=PersonalState.LOADED)


class SavedLooksTemplateSpecContract(BaseContractModel):
    """PR04: Saved outfit collections and looks canvas (Section 13.15, 13.16)."""
    screen_id: PersonalScreenId = Field(default=PersonalScreenId.PR04_SAVED_LOOKS)
    title: str = Field(default="Saved Looks")
    total_count: int
    collections: list[PersonalCollectionContract] = Field(default_factory=list)
    items: list[SavedLookContract] = Field(default_factory=list)
    active_collection: str | None = Field(default=None)
    state: PersonalState = Field(default=PersonalState.LOADED)


class SavedFashionTemplateSpecContract(BaseContractModel):
    """PR05: Saved editorial stories, trends, and inspiration (Section 13.17, 13.18)."""
    screen_id: PersonalScreenId = Field(default=PersonalScreenId.PR05_SAVED_FASHION)
    title: str = Field(default="Saved Fashion")
    active_tab: str = Field(default="all")
    available_tabs: list[str] = Field(
        default_factory=lambda: ["all", "stories", "collections", "trends", "brands"]
    )
    items: list[SavedFashionContract] = Field(default_factory=list)
    total_count: int
    state: PersonalState = Field(default=PersonalState.LOADED)


class WishlistTemplateSpecContract(BaseContractModel):
    """PR06: Commercial wishlist with real-time stock and price change tracking (Section 13.19 - 13.21)."""
    screen_id: PersonalScreenId = Field(default=PersonalScreenId.PR06_WISHLIST)
    title: str = Field(default="Wishlist")
    items: list[WishlistItemContract] = Field(default_factory=list)
    total_count: int
    available_count: int
    unavailable_count: int
    state: PersonalState = Field(default=PersonalState.LOADED)


class RecentlyViewedTemplateSpecContract(BaseContractModel):
    """PR07: Browsing activity history with privacy clear controls (Section 13.22 - 13.25)."""
    screen_id: PersonalScreenId = Field(default=PersonalScreenId.PR07_RECENTLY_VIEWED)
    title: str = Field(default="Recently Viewed")
    items: list[ActivityContract] = Field(default_factory=list)
    total_count: int
    active_filter: str | None = Field(default=None)
    can_clear_history: bool = Field(default=True)
    state: PersonalState = Field(default=PersonalState.LOADED)


class PreferencesTemplateSpecContract(BaseContractModel):
    """PR08: Modular explicit style and wardrobe preferences canvas (Section 13.26 - 13.28)."""
    screen_id: PersonalScreenId = Field(default=PersonalScreenId.PR08_PREFERENCES)
    title: str = Field(default="Preferences")
    explicit_preferences: ExplicitPreferencesContract
    inferred_preferences: InferredPreferencesContract
    available_styles: list[str] = Field(default_factory=list)
    available_categories: list[str] = Field(default_factory=list)
    available_colors: list[str] = Field(default_factory=list)
    available_fits: list[str] = Field(default_factory=list)
    available_materials: list[str] = Field(default_factory=list)
    available_contexts: list[str] = Field(default_factory=list)
    has_unsaved_changes: bool = Field(default=False)
    state: PersonalState = Field(default=PersonalState.LOADED)


class RecommendationPreferencesTemplateSpecContract(BaseContractModel):
    """PR09: Algorithmic recommendation tuning and transparency controls (Section 13.29 - 13.33)."""
    screen_id: PersonalScreenId = Field(default=PersonalScreenId.PR09_RECOMMENDATION_PREFERENCES)
    title: str = Field(default="Recommendation Preferences")
    settings: RecommendationPreferencesContract
    transparency_explanation: str
    can_reset_personalization: bool = Field(default=True)
    state: PersonalState = Field(default=PersonalState.LOADED)


class RegionalPreferencesTemplateSpecContract(BaseContractModel):
    """PR10: Regional fashion culture context preferences (Section 13.34 - 13.36)."""
    screen_id: PersonalScreenId = Field(default=PersonalScreenId.PR10_REGIONAL_PREFERENCES)
    title: str = Field(default="Regional Preferences")
    settings: RegionalPreferencesContract
    available_countries: list[str] = Field(default_factory=list)
    available_regions: list[str] = Field(default_factory=list)
    disclaimer: str
    state: PersonalState = Field(default=PersonalState.LOADED)


class AccountSettingsTemplateSpecContract(BaseContractModel):
    """PR11: Account, security, and notification settings (Section 13.39 - 13.44)."""
    screen_id: PersonalScreenId = Field(default=PersonalScreenId.PR11_ACCOUNT_SETTINGS)
    title: str = Field(default="Account Settings")
    settings: AccountSettingsContract
    categories: list[str] = Field(default_factory=list)
    has_unsaved_changes: bool = Field(default=False)
    state: PersonalState = Field(default=PersonalState.LOADED)


# ---------------------------------------------------------------------------
# Request & Response Mutation Payloads
# ---------------------------------------------------------------------------

class UpdateExplicitPreferencesRequestContract(BaseContractModel):
    """Payload for updating explicit style preferences."""
    styles: list[str] | None = Field(default=None)
    categories: list[str] | None = Field(default=None)
    colors: list[str] | None = Field(default=None)
    fits: list[str] | None = Field(default=None)
    materials: list[str] | None = Field(default=None)
    contexts: list[str] | None = Field(default=None)


class UpdateRecommendationPreferencesRequestContract(BaseContractModel):
    """Payload for modifying recommendation switches."""
    personalized_recommendations: bool | None = Field(default=None)
    use_style_preferences: bool | None = Field(default=None)
    use_regional_context: bool | None = Field(default=None)


class UpdateRegionalPreferencesRequestContract(BaseContractModel):
    """Payload for updating discovery regional preferences."""
    preferred_country: str | None = Field(default=None)
    preferred_state: str | None = Field(default=None)
    preferred_city: str | None = Field(default=None)
    regional_discovery_enabled: bool | None = Field(default=None)
    delivery_region: str | None = Field(default=None)


class UpdateAccountSettingsRequestContract(BaseContractModel):
    """Payload for updating account details and notifications."""
    display_name: str | None = Field(default=None)
    notifications_enabled: bool | None = Field(default=None)
    privacy_level: str | None = Field(default=None)
    two_factor_auth: bool | None = Field(default=None)
    activity_history_retention: str | None = Field(default=None)


class SavedItemToggleRequestContract(BaseContractModel):
    """Payload to add or toggle a saved product, look, fashion item, or wishlist item."""
    item_type: SavedItemType
    item_id: str
    target_collection_id: str | None = Field(default=None)


class SavedItemToggleResultContract(BaseContractModel):
    """Result of saving or removing an item."""
    item_type: SavedItemType
    item_id: str
    is_saved: bool
    message: str


class ClearHistoryRequestContract(BaseContractModel):
    """Request payload to clear browsing history."""
    entity_type: ActivityEntityType | None = Field(default=None)
