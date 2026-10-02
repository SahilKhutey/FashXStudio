"""Personalization, Profile & Saved Experience Domain Service — Phase 13.

Implements the personal space domain logic:
- User profile summary with identity, explicit style tags, and saved tallies (PR01).
- Personal Dashboard prioritizing Continue -> Saved -> Recommendations -> Recent Activity (PR02).
- Saved Products with availability tracking and filter/sort (PR03).
- Saved Looks with outfit collections and interactive action controls (PR04).
- Saved Fashion with multi-format tabs (stories, collections, trends, brands) (PR05).
- Shopping Wishlist with real-time commerce availability & alternative handling (PR06).
- Recently Viewed history with privacy controls and clear history capability (PR07).
- Explicit vs Inferred Preferences with strict boundary separation (PR08).
- Recommendation Preferences with transparency explanation & reset controls (PR09).
- Regional Preferences with strict distinction between preference and GPS location (PR10).
- Account Settings, security parameters, and privacy levels (PR11).
- In-place test fixture resetting for isolated, repeatable testing.
"""

from typing import Any
from copy import deepcopy

from schemas.visual.personal import (
    AccountSettingsContract,
    AccountSettingsTemplateSpecContract,
    ActivityAction,
    ActivityContract,
    ActivityEntityType,
    ExplicitPreferencesContract,
    InferredPreferencesContract,
    PersonalCollectionContract,
    PersonalDashboardTemplateSpecContract,
    PersonalScreenId,
    PersonalState,
    PreferencesTemplateSpecContract,
    ProfileTemplateSpecContract,
    RecentlyViewedTemplateSpecContract,
    RecommendationPreferencesContract,
    RecommendationPreferencesTemplateSpecContract,
    RegionalPreferencesContract,
    RegionalPreferencesTemplateSpecContract,
    SavedFashionContentType,
    SavedFashionContract,
    SavedFashionTemplateSpecContract,
    SavedItemToggleRequestContract,
    SavedItemToggleResultContract,
    SavedItemType,
    SavedLookContract,
    SavedLooksTemplateSpecContract,
    SavedProductContract,
    SavedProductsTemplateSpecContract,
    SavedSummaryContract,
    UpdateAccountSettingsRequestContract,
    UpdateExplicitPreferencesRequestContract,
    UpdateRecommendationPreferencesRequestContract,
    UpdateRegionalPreferencesRequestContract,
    WishlistItemContract,
    WishlistTemplateSpecContract,
)


# ---------------------------------------------------------------------------
# Initial Fixtures & Registries (Sections 13.5 - 13.55)
# ---------------------------------------------------------------------------

INITIAL_SAVED_PRODUCTS: list[SavedProductContract] = [
    SavedProductContract(
        id="sav_prd_01",
        product_id="prod-denim-01",
        brand="RawDenim Co.",
        name="Selvedge Oversized Denim Jacket",
        price=4999.0,
        currency="INR",
        image_url="https://images.fashx.studio/products/denim-01.jpg",
        is_saved=True,
        saved_state_label="Saved in Products",
        availability="in_stock",
        saved_at="2026-10-01T14:20:00Z",
    ),
    SavedProductContract(
        id="sav_prd_02",
        product_id="prd_pleated_trousers",
        brand="Atelier Minimal",
        name="Wide-Leg Pleated Trousers",
        price=180.0,
        currency="USD",
        image_url="https://images.fashx.studio/products/trousers-pleat-01.jpg",
        is_saved=True,
        saved_state_label="Saved in Products",
        availability="in_stock",
        saved_at="2026-09-28T11:15:00Z",
    ),
    SavedProductContract(
        id="sav_prd_03",
        product_id="prd_silk_skirt",
        brand="Maison L'Ombre",
        name="Silk Bias Midi Skirt",
        price=210.0,
        currency="USD",
        image_url="https://images.fashx.studio/products/skirt-silk-01.jpg",
        is_saved=True,
        saved_state_label="Saved in Products",
        availability="low_stock",
        saved_at="2026-09-25T16:40:00Z",
    ),
    SavedProductContract(
        id="sav_prd_04",
        product_id="prd_leather_tote",
        brand="Vanguard Objects",
        name="Sculptural Leather Tote",
        price=420.0,
        currency="USD",
        image_url="https://images.fashx.studio/products/bag-tote-01.jpg",
        is_saved=True,
        saved_state_label="Saved in Products",
        availability="out_of_stock",
        saved_at="2026-09-20T09:00:00Z",
    ),
]

INITIAL_SAVED_LOOKS: list[SavedLookContract] = [
    SavedLookContract(
        id="sav_look_01",
        look_id="look_monochrome_tailored",
        title="Monochrome Tailoring & Structured Wool",
        style="Minimal / Contemporary",
        image_url="https://images.fashx.studio/looks/look-mono-01.jpg",
        collection_id="col_01",
        items_count=3,
        supported_actions=["open", "edit", "duplicate", "share", "shop", "remove"],
        saved_at="2026-10-01T15:00:00Z",
    ),
    SavedLookContract(
        id="sav_look_02",
        look_id="look_weekend_cashmere",
        title="Weekend Relaxed Cashmere & Raw Denim",
        style="Casual Luxury",
        image_url="https://images.fashx.studio/looks/look-weekend-01.jpg",
        collection_id="col_03",
        items_count=4,
        supported_actions=["open", "edit", "duplicate", "share", "shop", "remove"],
        saved_at="2026-09-29T18:30:00Z",
    ),
    SavedLookContract(
        id="sav_look_03",
        look_id="look_evening_trench",
        title="Architectural Evening Trench",
        style="Avant-Garde",
        image_url="https://images.fashx.studio/looks/look-trench-01.jpg",
        collection_id="col_02",
        items_count=3,
        supported_actions=["open", "edit", "duplicate", "share", "shop", "remove"],
        saved_at="2026-09-22T20:10:00Z",
    ),
]

INITIAL_SAVED_FASHION: list[SavedFashionContract] = [
    SavedFashionContract(
        id="sav_fash_01",
        content_id="story_paris_outerwear",
        content_type=SavedFashionContentType.STORY,
        title="The Rise of Architectural Outerwear in Paris",
        author_or_brand="FashX Editorial",
        image_url="https://images.fashx.studio/editorial/paris-outerwear.jpg",
        saved_at="2026-10-01T08:15:00Z",
    ),
    SavedFashionContract(
        id="sav_fash_02",
        content_id="collection_fw26_tailoring",
        content_type=SavedFashionContentType.COLLECTION,
        title="Fall/Winter Capsule: Tailoring Without Constriction",
        author_or_brand="FashX Studio",
        image_url="https://images.fashx.studio/collections/fw26-capsule.jpg",
        saved_at="2026-09-30T10:00:00Z",
    ),
    SavedFashionContract(
        id="sav_fash_03",
        content_id="trend_neo_minimalism",
        content_type=SavedFashionContentType.TREND,
        title="Neo-Minimalism & Raw Wool Textures",
        author_or_brand="Trend Intelligence",
        image_url="https://images.fashx.studio/trends/neo-minimal.jpg",
        saved_at="2026-09-27T14:45:00Z",
    ),
    SavedFashionContract(
        id="sav_fash_04",
        content_id="brand_atelier_minimal",
        content_type=SavedFashionContentType.BRAND,
        title="Atelier Minimal: Artisan Spotlight",
        author_or_brand="Atelier Minimal",
        image_url="https://images.fashx.studio/brands/atelier-minimal.jpg",
        saved_at="2026-09-24T12:00:00Z",
    ),
]

INITIAL_WISHLIST: list[WishlistItemContract] = [
    WishlistItemContract(
        id="wish_01",
        product_id="prod-denim-01",
        brand="RawDenim Co.",
        name="Selvedge Oversized Denim Jacket",
        price=4999.0,
        currency="INR",
        image_url="https://images.fashx.studio/products/denim-01.jpg",
        availability="in_stock",
        is_available=True,
        availability_notice=None,
        alternative_product_id=None,
        added_at="2026-09-30T16:00:00Z",
    ),
    WishlistItemContract(
        id="wish_02",
        product_id="prd_square_loafers",
        brand="Forme Lab",
        name="Square-Toe Leather Loafers",
        price=290.0,
        currency="USD",
        image_url="https://images.fashx.studio/products/loafers-leather-01.jpg",
        availability="in_stock",
        is_available=True,
        availability_notice=None,
        alternative_product_id=None,
        added_at="2026-09-26T12:30:00Z",
    ),
    WishlistItemContract(
        id="wish_03",
        product_id="prd_silver_cuff",
        brand="Studio Oro",
        name="Architectural Silver Cuff",
        price=145.0,
        currency="USD",
        image_url="https://images.fashx.studio/products/cuff-silver-01.jpg",
        availability="out_of_stock",
        is_available=False,
        availability_notice="Out of stock - Restock expected in November",
        alternative_product_id="prd_saved_04",
        added_at="2026-09-18T19:00:00Z",
    ),
]

INITIAL_ACTIVITY: list[ActivityContract] = [
    ActivityContract(
        entity_id="prd_saved_01",
        entity_type=ActivityEntityType.PRODUCT,
        action=ActivityAction.VIEW,
        title="Oversized Cashmere Blazer",
        subtitle="Studio FashX",
        image_url="https://images.fashx.studio/products/blazer-cashmere-01.jpg",
        timestamp="2026-10-02T10:30:00Z",
        metadata={"category": "Outerwear"},
    ),
    ActivityContract(
        entity_id="sav_look_01",
        entity_type=ActivityEntityType.LOOK,
        action=ActivityAction.VIEW,
        title="Monochrome Tailoring & Structured Wool",
        subtitle="Look",
        image_url="https://images.fashx.studio/looks/look-mono-01.jpg",
        timestamp="2026-10-02T09:45:00Z",
        metadata={"style": "Minimal"},
    ),
    ActivityContract(
        entity_id="sav_fash_01",
        entity_type=ActivityEntityType.FASHION,
        action=ActivityAction.OPEN,
        title="The Rise of Architectural Outerwear in Paris",
        subtitle="Editorial Story",
        image_url="https://images.fashx.studio/editorial/paris-outerwear.jpg",
        timestamp="2026-10-02T08:15:00Z",
        metadata={"read_time": "4 min"},
    ),
    ActivityContract(
        entity_id="trd_neo_minimal",
        entity_type=ActivityEntityType.TREND,
        action=ActivityAction.SEARCH,
        title="Neo-Minimalism",
        subtitle="Trend Query",
        image_url="https://images.fashx.studio/trends/neo-minimal.jpg",
        timestamp="2026-10-01T21:00:00Z",
        metadata={"query": "Neo-Minimalism wool"},
    ),
]

INITIAL_COLLECTIONS: list[PersonalCollectionContract] = [
    PersonalCollectionContract(
        id="col_01",
        name="Autumn Capsule 2026",
        description="Tailored layers, structured outerwear, and neutral wools",
        item_count=4,
        cover_image_url="https://images.fashx.studio/collections/autumn-capsule.jpg",
        created_at="2026-09-15T10:00:00Z",
    ),
    PersonalCollectionContract(
        id="col_02",
        name="Paris Fashion Week Inspo",
        description="Editorial silhouettes, dramatic lapels, and trench coats",
        item_count=3,
        cover_image_url="https://images.fashx.studio/collections/paris-inspo.jpg",
        created_at="2026-09-20T14:30:00Z",
    ),
    PersonalCollectionContract(
        id="col_03",
        name="Daily Staples",
        description="Essential trousers, fine gauge knits, and comfortable loafers",
        item_count=5,
        cover_image_url="https://images.fashx.studio/collections/daily-staples.jpg",
        created_at="2026-09-01T09:00:00Z",
    ),
]

INITIAL_EXPLICIT_PREFERENCES = ExplicitPreferencesContract(
    styles=["Minimal", "Tailored", "Contemporary"],
    categories=["Outerwear", "Trousers", "Blazers", "Knitwear"],
    colors=["Black", "Charcoal", "Cream", "Camel"],
    fits=["Oversized", "Relaxed", "Architectural"],
    materials=["Cashmere", "Virgin Wool", "Silk", "Heavy Cotton"],
    contexts=["Urban Professional", "Gallery Opening", "Weekend Travel"],
)

INITIAL_INFERRED_PREFERENCES = InferredPreferencesContract(
    frequently_viewed_styles=["Minimal", "Tailored"],
    frequently_viewed_categories=["Outerwear", "Blazers"],
    frequently_viewed_colors=["Black", "Cream"],
    observation_notice="Inferred from browsing history. Does not alter your explicit style choices.",
)

INITIAL_RECOMMENDATION_PREFERENCES = RecommendationPreferencesContract(
    personalized_recommendations=True,
    use_style_preferences=True,
    use_regional_context=True,
    transparency_signals=["selected_styles", "saved_items", "recent_activity"],
)

INITIAL_REGIONAL_PREFERENCES = RegionalPreferencesContract(
    preferred_country="France",
    preferred_state="Île-de-France",
    preferred_city="Paris",
    regional_discovery_enabled=True,
    delivery_region="Europe - Western",
    disclaimer="Preferred region is a discovery preference, not current device GPS location.",
)

INITIAL_ACCOUNT_SETTINGS = AccountSettingsContract(
    user_id="usr_fashx_01",
    email="alexandra.chen@example.com",
    display_name="Alexandra Chen",
    notifications_enabled=True,
    privacy_level="standard",
    two_factor_auth=True,
    activity_history_retention="90_days",
    categories=["profile", "account", "notifications", "privacy", "security", "personalization"],
)


# ---------------------------------------------------------------------------
# Operational State Registries
# ---------------------------------------------------------------------------

SAVED_PRODUCTS_REGISTRY: dict[str, SavedProductContract] = {
    p.id: p.model_copy(deep=True) for p in INITIAL_SAVED_PRODUCTS
}
SAVED_LOOKS_REGISTRY: dict[str, SavedLookContract] = {
    l.id: l.model_copy(deep=True) for l in INITIAL_SAVED_LOOKS
}
SAVED_FASHION_REGISTRY: dict[str, SavedFashionContract] = {
    f.id: f.model_copy(deep=True) for f in INITIAL_SAVED_FASHION
}
WISHLIST_REGISTRY: dict[str, WishlistItemContract] = {
    w.id: w.model_copy(deep=True) for w in INITIAL_WISHLIST
}
ACTIVITY_REGISTRY: list[ActivityContract] = [
    a.model_copy(deep=True) for a in INITIAL_ACTIVITY
]
COLLECTIONS_REGISTRY: dict[str, PersonalCollectionContract] = {
    c.id: c.model_copy(deep=True) for c in INITIAL_COLLECTIONS
}

CURRENT_EXPLICIT_PREFERENCES: ExplicitPreferencesContract = INITIAL_EXPLICIT_PREFERENCES.model_copy(deep=True)
CURRENT_INFERRED_PREFERENCES: InferredPreferencesContract = INITIAL_INFERRED_PREFERENCES.model_copy(deep=True)
CURRENT_RECOMMENDATION_PREFERENCES: RecommendationPreferencesContract = INITIAL_RECOMMENDATION_PREFERENCES.model_copy(deep=True)
CURRENT_REGIONAL_PREFERENCES: RegionalPreferencesContract = INITIAL_REGIONAL_PREFERENCES.model_copy(deep=True)
CURRENT_ACCOUNT_SETTINGS: AccountSettingsContract = INITIAL_ACCOUNT_SETTINGS.model_copy(deep=True)


def reset_personal_fixtures() -> None:
    """Restore all personal space registries to pristine default states."""
    SAVED_PRODUCTS_REGISTRY.clear()
    for p in INITIAL_SAVED_PRODUCTS:
        SAVED_PRODUCTS_REGISTRY[p.id] = p.model_copy(deep=True)

    SAVED_LOOKS_REGISTRY.clear()
    for l in INITIAL_SAVED_LOOKS:
        SAVED_LOOKS_REGISTRY[l.id] = l.model_copy(deep=True)

    SAVED_FASHION_REGISTRY.clear()
    for f in INITIAL_SAVED_FASHION:
        SAVED_FASHION_REGISTRY[f.id] = f.model_copy(deep=True)

    WISHLIST_REGISTRY.clear()
    for w in INITIAL_WISHLIST:
        WISHLIST_REGISTRY[w.id] = w.model_copy(deep=True)

    ACTIVITY_REGISTRY.clear()
    ACTIVITY_REGISTRY.extend([a.model_copy(deep=True) for a in INITIAL_ACTIVITY])

    COLLECTIONS_REGISTRY.clear()
    for c in INITIAL_COLLECTIONS:
        COLLECTIONS_REGISTRY[c.id] = c.model_copy(deep=True)

    CURRENT_EXPLICIT_PREFERENCES.styles.clear()
    CURRENT_EXPLICIT_PREFERENCES.styles.extend(INITIAL_EXPLICIT_PREFERENCES.styles)
    CURRENT_EXPLICIT_PREFERENCES.categories.clear()
    CURRENT_EXPLICIT_PREFERENCES.categories.extend(INITIAL_EXPLICIT_PREFERENCES.categories)
    CURRENT_EXPLICIT_PREFERENCES.colors.clear()
    CURRENT_EXPLICIT_PREFERENCES.colors.extend(INITIAL_EXPLICIT_PREFERENCES.colors)
    CURRENT_EXPLICIT_PREFERENCES.fits.clear()
    CURRENT_EXPLICIT_PREFERENCES.fits.extend(INITIAL_EXPLICIT_PREFERENCES.fits)
    CURRENT_EXPLICIT_PREFERENCES.materials.clear()
    CURRENT_EXPLICIT_PREFERENCES.materials.extend(INITIAL_EXPLICIT_PREFERENCES.materials)
    CURRENT_EXPLICIT_PREFERENCES.contexts.clear()
    CURRENT_EXPLICIT_PREFERENCES.contexts.extend(INITIAL_EXPLICIT_PREFERENCES.contexts)

    CURRENT_INFERRED_PREFERENCES.frequently_viewed_styles.clear()
    CURRENT_INFERRED_PREFERENCES.frequently_viewed_styles.extend(INITIAL_INFERRED_PREFERENCES.frequently_viewed_styles)
    CURRENT_INFERRED_PREFERENCES.frequently_viewed_categories.clear()
    CURRENT_INFERRED_PREFERENCES.frequently_viewed_categories.extend(INITIAL_INFERRED_PREFERENCES.frequently_viewed_categories)
    CURRENT_INFERRED_PREFERENCES.frequently_viewed_colors.clear()
    CURRENT_INFERRED_PREFERENCES.frequently_viewed_colors.extend(INITIAL_INFERRED_PREFERENCES.frequently_viewed_colors)
    CURRENT_INFERRED_PREFERENCES.observation_notice = INITIAL_INFERRED_PREFERENCES.observation_notice

    CURRENT_RECOMMENDATION_PREFERENCES.personalized_recommendations = INITIAL_RECOMMENDATION_PREFERENCES.personalized_recommendations
    CURRENT_RECOMMENDATION_PREFERENCES.use_style_preferences = INITIAL_RECOMMENDATION_PREFERENCES.use_style_preferences
    CURRENT_RECOMMENDATION_PREFERENCES.use_regional_context = INITIAL_RECOMMENDATION_PREFERENCES.use_regional_context

    CURRENT_REGIONAL_PREFERENCES.preferred_country = INITIAL_REGIONAL_PREFERENCES.preferred_country
    CURRENT_REGIONAL_PREFERENCES.preferred_state = INITIAL_REGIONAL_PREFERENCES.preferred_state
    CURRENT_REGIONAL_PREFERENCES.preferred_city = INITIAL_REGIONAL_PREFERENCES.preferred_city
    CURRENT_REGIONAL_PREFERENCES.regional_discovery_enabled = INITIAL_REGIONAL_PREFERENCES.regional_discovery_enabled
    CURRENT_REGIONAL_PREFERENCES.delivery_region = INITIAL_REGIONAL_PREFERENCES.delivery_region

    CURRENT_ACCOUNT_SETTINGS.display_name = INITIAL_ACCOUNT_SETTINGS.display_name
    CURRENT_ACCOUNT_SETTINGS.notifications_enabled = INITIAL_ACCOUNT_SETTINGS.notifications_enabled
    CURRENT_ACCOUNT_SETTINGS.privacy_level = INITIAL_ACCOUNT_SETTINGS.privacy_level
    CURRENT_ACCOUNT_SETTINGS.two_factor_auth = INITIAL_ACCOUNT_SETTINGS.two_factor_auth
    CURRENT_ACCOUNT_SETTINGS.activity_history_retention = INITIAL_ACCOUNT_SETTINGS.activity_history_retention


# ---------------------------------------------------------------------------
# Domain Service Implementation: PR01 - PR11
# ---------------------------------------------------------------------------

def compute_saved_summary() -> SavedSummaryContract:
    """Compute aggregate counts for saved products, looks, fashion, and wishlist."""
    return SavedSummaryContract(
        products_count=len(SAVED_PRODUCTS_REGISTRY),
        looks_count=len(SAVED_LOOKS_REGISTRY),
        fashion_count=len(SAVED_FASHION_REGISTRY),
        wishlist_count=len(WISHLIST_REGISTRY),
        collections_count=len(COLLECTIONS_REGISTRY),
    )


def get_profile_template(user_id: str = "usr_fashx_01") -> ProfileTemplateSpecContract:
    """PR01: Construct the authoritative profile view specification (Section 13.6 - 13.8)."""
    summary = compute_saved_summary()
    recent_preview = sorted(ACTIVITY_REGISTRY, key=lambda a: a.timestamp, reverse=True)[:3]
    return ProfileTemplateSpecContract(
        screen_id=PersonalScreenId.PR01_PROFILE,
        user_id=CURRENT_ACCOUNT_SETTINGS.user_id,
        display_name=CURRENT_ACCOUNT_SETTINGS.display_name,
        avatar_url="https://images.fashx.studio/avatars/alexandra.jpg",
        bio="Minimalist wardrobe enthusiast & contemporary silhouette curator.",
        style_tags=list(CURRENT_EXPLICIT_PREFERENCES.styles),
        saved_summary=summary,
        preferences_preview=[
            *CURRENT_EXPLICIT_PREFERENCES.styles[:2],
            *CURRENT_EXPLICIT_PREFERENCES.categories[:2],
        ],
        recent_activity_preview=recent_preview,
        regional_context=CURRENT_REGIONAL_PREFERENCES,
        state=PersonalState.LOADED,
    )


def get_personal_dashboard_template(
    user_id: str = "usr_fashx_01",
    fail_recommendations: bool = False,
) -> PersonalDashboardTemplateSpecContract:
    """PR02: Personal dashboard strictly following priority: Continue -> Saved -> Recommendations -> Recent (Section 13.9 - 13.11)."""
    # 1. Continue Exploring (top priority)
    continue_exploring = [
        {
            "id": "cont_01",
            "type": "look",
            "title": "Monochrome Tailoring",
            "subtitle": "Resume Outfit Editing",
            "image_url": "https://images.fashx.studio/looks/look-mono-01.jpg",
        },
        {
            "id": "cont_02",
            "type": "product",
            "title": "Oversized Cashmere Blazer",
            "subtitle": "Viewed 2 hours ago",
            "image_url": "https://images.fashx.studio/products/blazer-cashmere-01.jpg",
        },
        {
            "id": "cont_03",
            "type": "story",
            "title": "Paris Outerwear Editorial",
            "subtitle": "Continue reading (2 min left)",
            "image_url": "https://images.fashx.studio/editorial/paris-outerwear.jpg",
        },
    ]

    # 2. Saved Items Preview
    saved_preview = [
        {
            "id": p.id,
            "title": p.name,
            "brand": p.brand,
            "type": "product",
            "price": p.price,
            "image_url": p.image_url,
        }
        for p in list(SAVED_PRODUCTS_REGISTRY.values())[:2]
    ] + [
        {
            "id": l.id,
            "title": l.title,
            "brand": l.style,
            "type": "look",
            "price": None,
            "image_url": l.image_url,
        }
        for l in list(SAVED_LOOKS_REGISTRY.values())[:1]
    ]

    # 3. Recommendations (Gracefully degrades on failure per Section 13.51)
    if fail_recommendations:
        rec_products: list[SavedProductContract] = []
        rec_looks: list[SavedLookContract] = []
        rec_state = PersonalState.ERROR
    else:
        rec_products = list(SAVED_PRODUCTS_REGISTRY.values())[:3]
        rec_looks = list(SAVED_LOOKS_REGISTRY.values())[:2]
        rec_state = PersonalState.LOADED

    # 4. Recently Viewed
    recent_activity = sorted(ACTIVITY_REGISTRY, key=lambda a: a.timestamp, reverse=True)[:4]

    # 5. Regional Highlights & AI suggestions
    regional_highlights = [
        {
            "region": "Paris",
            "headline": "Oversized Trench Trend surging in Le Marais",
            "trend_score": "+38%",
        }
    ]
    ai_suggestions = [
        {
            "prompt": "Style your Oversized Cashmere Blazer for evening",
            "action": "open_style_assistant",
        }
    ]

    module_states = {
        "continue_exploring": PersonalState.LOADED,
        "saved_preview": PersonalState.LOADED,
        "recommendations": rec_state,
        "recently_viewed": PersonalState.LOADED,
        "regional_highlights": PersonalState.LOADED,
        "ai_suggestions": PersonalState.LOADED,
    }

    overall_state = PersonalState.PARTIAL if fail_recommendations else PersonalState.LOADED

    return PersonalDashboardTemplateSpecContract(
        screen_id=PersonalScreenId.PR02_PERSONAL_DASHBOARD,
        welcome_title=f"Welcome back, {CURRENT_ACCOUNT_SETTINGS.display_name.split()[0]}",
        continue_exploring=continue_exploring,
        recommended_products=rec_products,
        recommended_looks=rec_looks,
        saved_preview=saved_preview,
        recently_viewed=recent_activity,
        regional_highlights=regional_highlights,
        ai_suggestions=ai_suggestions,
        module_states=module_states,
        state=overall_state,
    )


def get_saved_products_template(
    filter_category: str | None = None,
    sort_by: str = "recently_saved",
) -> SavedProductsTemplateSpecContract:
    """PR03: Retrieve saved products with filtering and sorting (Section 13.13, 13.14)."""
    items = list(SAVED_PRODUCTS_REGISTRY.values())

    if filter_category:
        cat_lower = filter_category.lower()
        items = [i for i in items if cat_lower in i.name.lower() or cat_lower in i.brand.lower()]

    if sort_by == "price_asc":
        items = sorted(items, key=lambda x: x.price)
    elif sort_by == "price_desc":
        items = sorted(items, key=lambda x: x.price, reverse=True)
    elif sort_by == "name":
        items = sorted(items, key=lambda x: x.name)
    else:  # recently_saved
        items = list(reversed(items))

    state = PersonalState.EMPTY if len(items) == 0 else PersonalState.LOADED

    return SavedProductsTemplateSpecContract(
        screen_id=PersonalScreenId.PR03_SAVED_PRODUCTS,
        title="Saved Products",
        total_count=len(items),
        items=items,
        active_filter=filter_category,
        active_sort=sort_by,
        state=state,
    )


def get_personal_saved_looks_template(
    collection_id: str | None = None,
) -> SavedLooksTemplateSpecContract:
    """PR04: Retrieve saved outfit looks grouped or filtered by collection (Section 13.15, 13.16)."""
    looks = list(SAVED_LOOKS_REGISTRY.values())
    collections = list(COLLECTIONS_REGISTRY.values())

    if collection_id:
        looks = [l for l in looks if l.collection_id == collection_id]

    state = PersonalState.EMPTY if len(looks) == 0 else PersonalState.LOADED

    return SavedLooksTemplateSpecContract(
        screen_id=PersonalScreenId.PR04_SAVED_LOOKS,
        title="Saved Looks",
        total_count=len(looks),
        collections=collections,
        items=looks,
        active_collection=collection_id,
        state=state,
    )


get_saved_looks_template = get_personal_saved_looks_template


def get_saved_fashion_template(tab: str = "all") -> SavedFashionTemplateSpecContract:
    """PR05: Retrieve saved editorial, collections, trends, and brand stories (Section 13.17, 13.18)."""
    items = list(SAVED_FASHION_REGISTRY.values())

    tab_normalized = tab.lower()
    if tab_normalized in ["stories", "story"]:
        items = [i for i in items if i.content_type == SavedFashionContentType.STORY]
    elif tab_normalized in ["collections", "collection"]:
        items = [i for i in items if i.content_type == SavedFashionContentType.COLLECTION]
    elif tab_normalized in ["trends", "trend"]:
        items = [i for i in items if i.content_type == SavedFashionContentType.TREND]
    elif tab_normalized in ["brands", "brand"]:
        items = [i for i in items if i.content_type == SavedFashionContentType.BRAND]

    state = PersonalState.EMPTY if len(items) == 0 else PersonalState.LOADED

    return SavedFashionTemplateSpecContract(
        screen_id=PersonalScreenId.PR05_SAVED_FASHION,
        title="Saved Fashion",
        active_tab=tab_normalized,
        available_tabs=["all", "stories", "collections", "trends", "brands"],
        items=items,
        total_count=len(items),
        state=state,
    )


def get_personal_wishlist_template() -> WishlistTemplateSpecContract:
    """PR06: Retrieve shopping wishlist with live availability and alternative indicators (Section 13.19 - 13.21)."""
    items = list(WISHLIST_REGISTRY.values())
    avail_count = sum(1 for i in items if i.is_available)
    unavail_count = sum(1 for i in items if not i.is_available)

    state = PersonalState.EMPTY if len(items) == 0 else PersonalState.LOADED

    return WishlistTemplateSpecContract(
        screen_id=PersonalScreenId.PR06_WISHLIST,
        title="Wishlist",
        items=items,
        total_count=len(items),
        available_count=avail_count,
        unavailable_count=unavail_count,
        state=state,
    )


get_wishlist_template = get_personal_wishlist_template


def get_recently_viewed_template(
    entity_type: str | None = None,
) -> RecentlyViewedTemplateSpecContract:
    """PR07: Browsing history with explicit privacy boundaries (Section 13.22 - 13.25)."""
    items = sorted(ACTIVITY_REGISTRY, key=lambda a: a.timestamp, reverse=True)

    if entity_type:
        et_lower = entity_type.lower()
        items = [i for i in items if i.entity_type.value == et_lower]

    state = PersonalState.EMPTY if len(items) == 0 else PersonalState.LOADED

    return RecentlyViewedTemplateSpecContract(
        screen_id=PersonalScreenId.PR07_RECENTLY_VIEWED,
        title="Recently Viewed",
        items=items,
        total_count=len(items),
        active_filter=entity_type,
        can_clear_history=True,
        state=state,
    )


def clear_recently_viewed_history(entity_type: str | None = None) -> dict[str, Any]:
    """Clear browsing activity history completely or by target entity type (Section 13.25)."""
    global ACTIVITY_REGISTRY
    if entity_type:
        et_lower = entity_type.lower()
        ACTIVITY_REGISTRY = [a for a in ACTIVITY_REGISTRY if a.entity_type.value != et_lower]
        msg = f"Cleared history for {entity_type}"
    else:
        ACTIVITY_REGISTRY.clear()
        msg = "All browsing history cleared"

    return {"status": "success", "message": msg, "remaining_count": len(ACTIVITY_REGISTRY)}


def get_preferences_template() -> PreferencesTemplateSpecContract:
    """PR08: Modular explicit preferences canvas strictly separated from inferred history (Section 13.26 - 13.28)."""
    return PreferencesTemplateSpecContract(
        screen_id=PersonalScreenId.PR08_PREFERENCES,
        title="Preferences",
        explicit_preferences=CURRENT_EXPLICIT_PREFERENCES,
        inferred_preferences=CURRENT_INFERRED_PREFERENCES,
        available_styles=["Minimal", "Tailored", "Contemporary", "Streetwear", "Formal", "Avant-Garde", "Bohemian"],
        available_categories=["Outerwear", "Trousers", "Blazers", "Knitwear", "Dresses", "Footwear", "Accessories"],
        available_colors=["Black", "Charcoal", "Cream", "Camel", "Navy", "Olive", "White", "Burgundy"],
        available_fits=["Oversized", "Relaxed", "Architectural", "Slim", "Regular"],
        available_materials=["Cashmere", "Virgin Wool", "Silk", "Heavy Cotton", "Linen", "Leather"],
        available_contexts=["Urban Professional", "Gallery Opening", "Weekend Travel", "Evening Event", "Casual Daily"],
        has_unsaved_changes=False,
        state=PersonalState.LOADED,
    )


def update_explicit_preferences(
    payload: UpdateExplicitPreferencesRequestContract,
) -> PreferencesTemplateSpecContract:
    """Update user's explicit style and wardrobe preferences (Section 13.27, 13.43)."""
    if payload.styles is not None:
        CURRENT_EXPLICIT_PREFERENCES.styles.clear()
        CURRENT_EXPLICIT_PREFERENCES.styles.extend(payload.styles)
    if payload.categories is not None:
        CURRENT_EXPLICIT_PREFERENCES.categories.clear()
        CURRENT_EXPLICIT_PREFERENCES.categories.extend(payload.categories)
    if payload.colors is not None:
        CURRENT_EXPLICIT_PREFERENCES.colors.clear()
        CURRENT_EXPLICIT_PREFERENCES.colors.extend(payload.colors)
    if payload.fits is not None:
        CURRENT_EXPLICIT_PREFERENCES.fits.clear()
        CURRENT_EXPLICIT_PREFERENCES.fits.extend(payload.fits)
    if payload.materials is not None:
        CURRENT_EXPLICIT_PREFERENCES.materials.clear()
        CURRENT_EXPLICIT_PREFERENCES.materials.extend(payload.materials)
    if payload.contexts is not None:
        CURRENT_EXPLICIT_PREFERENCES.contexts.clear()
        CURRENT_EXPLICIT_PREFERENCES.contexts.extend(payload.contexts)

    template = get_preferences_template()
    template.state = PersonalState.SAVED
    return template


def get_recommendation_preferences_template() -> RecommendationPreferencesTemplateSpecContract:
    """PR09: Algorithmic recommendation controls with transparency signals (Section 13.29 - 13.31)."""
    explanation = (
        "Recommendations use: "
        + ("Selected styles, " if CURRENT_RECOMMENDATION_PREFERENCES.use_style_preferences else "")
        + ("Saved items & wishlist, " if CURRENT_RECOMMENDATION_PREFERENCES.personalized_recommendations else "")
        + ("Regional fashion context. " if CURRENT_RECOMMENDATION_PREFERENCES.use_regional_context else "")
    )

    return RecommendationPreferencesTemplateSpecContract(
        screen_id=PersonalScreenId.PR09_RECOMMENDATION_PREFERENCES,
        title="Recommendation Preferences",
        settings=CURRENT_RECOMMENDATION_PREFERENCES,
        transparency_explanation=explanation,
        can_reset_personalization=True,
        state=PersonalState.LOADED,
    )


def update_recommendation_preferences(
    payload: UpdateRecommendationPreferencesRequestContract,
) -> RecommendationPreferencesTemplateSpecContract:
    """Update recommendation toggle controls (Section 13.30)."""
    if payload.personalized_recommendations is not None:
        CURRENT_RECOMMENDATION_PREFERENCES.personalized_recommendations = payload.personalized_recommendations
    if payload.use_style_preferences is not None:
        CURRENT_RECOMMENDATION_PREFERENCES.use_style_preferences = payload.use_style_preferences
    if payload.use_regional_context is not None:
        CURRENT_RECOMMENDATION_PREFERENCES.use_regional_context = payload.use_regional_context

    template = get_recommendation_preferences_template()
    template.state = PersonalState.SAVED
    return template


def reset_personalization_signals() -> RecommendationPreferencesTemplateSpecContract:
    """PR09 Reset: Clear all inferred signals and restore baseline recommendation state (Section 13.33)."""
    CURRENT_INFERRED_PREFERENCES.frequently_viewed_styles.clear()
    CURRENT_INFERRED_PREFERENCES.frequently_viewed_categories.clear()
    CURRENT_INFERRED_PREFERENCES.frequently_viewed_colors.clear()
    CURRENT_INFERRED_PREFERENCES.observation_notice = "All inferred browsing signals have been reset."

    template = get_recommendation_preferences_template()
    template.state = PersonalState.SAVED
    return template


def get_regional_preferences_template() -> RegionalPreferencesTemplateSpecContract:
    """PR10: Regional discovery context strictly decoupled from physical GPS location (Section 13.34 - 13.36)."""
    return RegionalPreferencesTemplateSpecContract(
        screen_id=PersonalScreenId.PR10_REGIONAL_PREFERENCES,
        title="Regional Preferences",
        settings=CURRENT_REGIONAL_PREFERENCES,
        available_countries=["France", "Japan", "United Kingdom", "United States", "Italy", "South Korea"],
        available_regions=["Europe - Western", "East Asia", "North America", "Scandinavia"],
        disclaimer=CURRENT_REGIONAL_PREFERENCES.disclaimer,
        state=PersonalState.LOADED,
    )


def update_regional_preferences(
    payload: UpdateRegionalPreferencesRequestContract,
) -> RegionalPreferencesTemplateSpecContract:
    """Update regional fashion context preferences (Section 13.34)."""
    if payload.preferred_country is not None:
        CURRENT_REGIONAL_PREFERENCES.preferred_country = payload.preferred_country
    if payload.preferred_state is not None:
        CURRENT_REGIONAL_PREFERENCES.preferred_state = payload.preferred_state
    if payload.preferred_city is not None:
        CURRENT_REGIONAL_PREFERENCES.preferred_city = payload.preferred_city
    if payload.regional_discovery_enabled is not None:
        CURRENT_REGIONAL_PREFERENCES.regional_discovery_enabled = payload.regional_discovery_enabled
    if payload.delivery_region is not None:
        CURRENT_REGIONAL_PREFERENCES.delivery_region = payload.delivery_region

    template = get_regional_preferences_template()
    template.state = PersonalState.SAVED
    return template


def get_account_settings_template() -> AccountSettingsTemplateSpecContract:
    """PR11: Account security, notification preferences, and privacy controls (Section 13.39 - 13.41)."""
    return AccountSettingsTemplateSpecContract(
        screen_id=PersonalScreenId.PR11_ACCOUNT_SETTINGS,
        title="Account Settings",
        settings=CURRENT_ACCOUNT_SETTINGS,
        categories=CURRENT_ACCOUNT_SETTINGS.categories,
        has_unsaved_changes=False,
        state=PersonalState.LOADED,
    )


def update_account_settings(
    payload: UpdateAccountSettingsRequestContract,
) -> AccountSettingsTemplateSpecContract:
    """Update account settings parameters (Section 13.41, 13.43)."""
    if payload.display_name is not None:
        CURRENT_ACCOUNT_SETTINGS.display_name = payload.display_name
    if payload.notifications_enabled is not None:
        CURRENT_ACCOUNT_SETTINGS.notifications_enabled = payload.notifications_enabled
    if payload.privacy_level is not None:
        CURRENT_ACCOUNT_SETTINGS.privacy_level = payload.privacy_level
    if payload.two_factor_auth is not None:
        CURRENT_ACCOUNT_SETTINGS.two_factor_auth = payload.two_factor_auth
    if payload.activity_history_retention is not None:
        CURRENT_ACCOUNT_SETTINGS.activity_history_retention = payload.activity_history_retention

    template = get_account_settings_template()
    template.state = PersonalState.SAVED
    return template



def toggle_saved_item(payload: SavedItemToggleRequestContract) -> SavedItemToggleResultContract:
    """Toggle save state for a product, look, fashion item, or wishlist item (Section 13.12 - 13.20)."""
    item_type = payload.item_type
    item_id = payload.item_id

    if item_type == SavedItemType.PRODUCT:
        if item_id in SAVED_PRODUCTS_REGISTRY:
            del SAVED_PRODUCTS_REGISTRY[item_id]
            return SavedItemToggleResultContract(
                item_type=item_type,
                item_id=item_id,
                is_saved=False,
                message=f"Removed product {item_id} from saved items",
            )
        else:
            new_item = SavedProductContract(
                id=item_id,
                product_id=item_id,
                brand="Studio FashX",
                name="Newly Saved Garment",
                price=195.0,
                currency="USD",
                image_url="https://images.fashx.studio/products/new-saved.jpg",
                is_saved=True,
                saved_state_label="Saved in Products",
                availability="in_stock",
                saved_at="2026-10-02T11:00:00Z",
            )
            SAVED_PRODUCTS_REGISTRY[item_id] = new_item
            return SavedItemToggleResultContract(
                item_type=item_type,
                item_id=item_id,
                is_saved=True,
                message=f"Saved product {item_id} to saved items",
            )

    elif item_type == SavedItemType.LOOK:
        if item_id in SAVED_LOOKS_REGISTRY:
            del SAVED_LOOKS_REGISTRY[item_id]
            return SavedItemToggleResultContract(
                item_type=item_type,
                item_id=item_id,
                is_saved=False,
                message=f"Removed look {item_id} from saved looks",
            )
        else:
            new_look = SavedLookContract(
                id=item_id,
                look_id=item_id,
                title="Curated Styled Look",
                style="Contemporary",
                image_url="https://images.fashx.studio/looks/new-look.jpg",
                collection_id=payload.target_collection_id or "col_01",
                items_count=3,
                supported_actions=["open", "edit", "duplicate", "share", "shop", "remove"],
                saved_at="2026-10-02T11:00:00Z",
            )
            SAVED_LOOKS_REGISTRY[item_id] = new_look
            return SavedItemToggleResultContract(
                item_type=item_type,
                item_id=item_id,
                is_saved=True,
                message=f"Saved look {item_id} to saved looks",
            )

    elif item_type == SavedItemType.FASHION:
        if item_id in SAVED_FASHION_REGISTRY:
            del SAVED_FASHION_REGISTRY[item_id]
            return SavedItemToggleResultContract(
                item_type=item_type,
                item_id=item_id,
                is_saved=False,
                message=f"Removed fashion content {item_id} from saved fashion",
            )
        else:
            new_fashion = SavedFashionContract(
                id=item_id,
                content_id=item_id,
                content_type=SavedFashionContentType.STORY,
                title="Saved Fashion Story",
                author_or_brand="FashX Studio",
                image_url="https://images.fashx.studio/editorial/new-story.jpg",
                saved_at="2026-10-02T11:00:00Z",
            )
            SAVED_FASHION_REGISTRY[item_id] = new_fashion
            return SavedItemToggleResultContract(
                item_type=item_type,
                item_id=item_id,
                is_saved=True,
                message=f"Saved fashion content {item_id} to saved fashion",
            )

    else:  # WISHLIST
        if item_id in WISHLIST_REGISTRY:
            del WISHLIST_REGISTRY[item_id]
            return SavedItemToggleResultContract(
                item_type=item_type,
                item_id=item_id,
                is_saved=False,
                message=f"Removed product {item_id} from wishlist",
            )
        else:
            new_wish = WishlistItemContract(
                id=item_id,
                product_id=item_id,
                brand="Selected Brand",
                name="Wishlist Product Item",
                price=250.0,
                currency="USD",
                image_url="https://images.fashx.studio/products/wishlist-item.jpg",
                availability="in_stock",
                is_available=True,
                availability_notice=None,
                alternative_product_id=None,
                added_at="2026-10-02T11:00:00Z",
            )
            WISHLIST_REGISTRY[item_id] = new_wish
            return SavedItemToggleResultContract(
                item_type=item_type,
                item_id=item_id,
                is_saved=True,
                message=f"Added product {item_id} to wishlist",
            )


def remove_saved_item(item_type: SavedItemType, item_id: str) -> SavedItemToggleResultContract:
    """Explicitly remove an item from its respective saved registry (Section 13.16, 13.20)."""
    if item_type == SavedItemType.PRODUCT:
        SAVED_PRODUCTS_REGISTRY.pop(item_id, None)
    elif item_type == SavedItemType.LOOK:
        SAVED_LOOKS_REGISTRY.pop(item_id, None)
    elif item_type == SavedItemType.FASHION:
        SAVED_FASHION_REGISTRY.pop(item_id, None)
    elif item_type == SavedItemType.WISHLIST:
        WISHLIST_REGISTRY.pop(item_id, None)

    return SavedItemToggleResultContract(
        item_type=item_type,
        item_id=item_id,
        is_saved=False,
        message=f"Successfully removed {item_id} from {item_type.value}",
    )


def record_activity(
    entity_id: str,
    entity_type: ActivityEntityType,
    action: ActivityAction,
    title: str,
    subtitle: str | None = None,
    image_url: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ActivityContract:
    """Record a user browsing/interaction event without conflating viewing with liking (Section 13.23, 13.24)."""
    activity = ActivityContract(
        entity_id=entity_id,
        entity_type=entity_type,
        action=action,
        title=title,
        subtitle=subtitle,
        image_url=image_url,
        timestamp="2026-10-02T12:00:00Z",
        metadata=metadata or {},
    )
    ACTIVITY_REGISTRY.append(activity)
    return activity
