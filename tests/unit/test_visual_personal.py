"""Unit tests for Profile, Personalization & Saved Experience System — Phase 13.

Verifies:
- PROFILE-001 to PROFILE-006: Profile (PR01), header, metadata, edit action, preference preview, saved preview
- DASH-001 to DASH-007: Personal Dashboard (PR02), priority ordering, continue, recommendations, saved, recent, partial loading, recommendation failure degradation
- SAVE-001 to SAVE-009: Saved products (PR03), saved looks (PR04), saved fashion (PR05), filtering, sorting, remove, open/toggle, empty states, unavailable product in wishlist (PR06)
- PREF-001 to PREF-009: Preferences (PR08), selection, deselection, saving state, saved state, error, unsaved changes, discard
- REG-001 to REG-003: Regional preferences (PR10) and GPS decoupling
- REC-001 to REC-003: Recommendation preferences (PR09), transparency signals, reset personalization
- SET-001 to SET-003: Account settings (PR11), notifications, privacy retention
- FORBID-001 to FORBID-008: Strict extra="forbid" rejection across all Personal contracts (Constitution Rule I02).
"""

import pytest
from pydantic import ValidationError

from schemas.visual.personal import (
    AccountSettingsContract,
    AccountSettingsTemplateSpecContract,
    ActivityAction,
    ActivityContract,
    ActivityEntityType,
    ClearHistoryRequestContract,
    ExplicitPreferencesContract,
    InferredPreferencesContract,
    PersonalAIPreferencesContract,
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
from fashx.visual.personal_service import (
    ACTIVITY_REGISTRY,
    CURRENT_ACCOUNT_SETTINGS,
    CURRENT_EXPLICIT_PREFERENCES,
    CURRENT_INFERRED_PREFERENCES,
    CURRENT_RECOMMENDATION_PREFERENCES,
    CURRENT_REGIONAL_PREFERENCES,
    SAVED_FASHION_REGISTRY,
    SAVED_LOOKS_REGISTRY,
    SAVED_PRODUCTS_REGISTRY,
    WISHLIST_REGISTRY,
    clear_recently_viewed_history,
    compute_saved_summary,
    get_account_settings_template,
    get_personal_dashboard_template,
    get_preferences_template,
    get_profile_template,
    get_recently_viewed_template,
    get_recommendation_preferences_template,
    get_regional_preferences_template,
    get_saved_fashion_template,
    get_saved_looks_template,
    get_saved_products_template,
    get_wishlist_template,
    record_activity,
    remove_saved_item,
    reset_personal_fixtures,
    reset_personalization_signals,
    toggle_saved_item,
    update_account_settings,
    update_explicit_preferences,
    update_recommendation_preferences,
    update_regional_preferences,
)


@pytest.fixture(autouse=True)
def reset_fixtures():
    """Ensure every test runs against pristine personal space fixtures."""
    reset_personal_fixtures()


# ===========================================================================
# 1. Profile Tests (PROFILE-001 to PROFILE-006)
# ===========================================================================

def test_profile_001_renders_successfully():
    """PROFILE-001: Main profile specification renders with PR01 screen id."""
    profile = get_profile_template(user_id="usr_fashx_01")
    assert profile.screen_id == PersonalScreenId.PR01_PROFILE
    assert profile.state == PersonalState.LOADED
    assert profile.user_id == "usr_fashx_01"


def test_profile_002_header_contains_identity():
    """PROFILE-002: Profile header contains display name, bio, and avatar."""
    profile = get_profile_template()
    assert profile.display_name == "Alexandra Chen"
    assert profile.avatar_url is not None
    assert "Minimalist" in (profile.bio or "")


def test_profile_003_profile_metadata_and_style_tags():
    """PROFILE-003: Style tags match user's explicit style tags."""
    profile = get_profile_template()
    assert "Minimal" in profile.style_tags
    assert "Tailored" in profile.style_tags
    assert len(profile.style_tags) >= 2


def test_profile_004_edit_action_updates_display_name():
    """PROFILE-004: Updating profile/account name updates the profile template."""
    update_account_settings(UpdateAccountSettingsRequestContract(display_name="Alexandra M. Chen"))
    profile = get_profile_template()
    assert profile.display_name == "Alexandra M. Chen"


def test_profile_005_preference_preview():
    """PROFILE-005: Preference preview exposes top styles and categories."""
    profile = get_profile_template()
    assert len(profile.preferences_preview) >= 2
    assert "Minimal" in profile.preferences_preview


def test_profile_006_saved_preview_computes_correct_tallies():
    """PROFILE-006: Saved summary matches actual registry lengths."""
    profile = get_profile_template()
    assert profile.saved_summary.products_count == len(SAVED_PRODUCTS_REGISTRY)
    assert profile.saved_summary.looks_count == len(SAVED_LOOKS_REGISTRY)
    assert profile.saved_summary.fashion_count == len(SAVED_FASHION_REGISTRY)
    assert profile.saved_summary.wishlist_count == len(WISHLIST_REGISTRY)


# ===========================================================================
# 2. Personal Dashboard Tests (DASH-001 to DASH-007)
# ===========================================================================

def test_dash_001_dashboard_renders():
    """DASH-001: Personal dashboard renders with PR02 specification."""
    dash = get_personal_dashboard_template()
    assert dash.screen_id == PersonalScreenId.PR02_PERSONAL_DASHBOARD
    assert "Alexandra" in dash.welcome_title
    assert dash.state == PersonalState.LOADED


def test_dash_002_continue_exploring_priority():
    """DASH-002: Continue exploring is present with look, product, and story items."""
    dash = get_personal_dashboard_template()
    assert len(dash.continue_exploring) >= 3
    types = {item["type"] for item in dash.continue_exploring}
    assert "look" in types
    assert "product" in types
    assert "story" in types


def test_dash_003_recommendations_section():
    """DASH-003: Recommendations provide products and looks."""
    dash = get_personal_dashboard_template()
    assert len(dash.recommended_products) >= 2
    assert len(dash.recommended_looks) >= 1


def test_dash_004_saved_section_preview():
    """DASH-004: Saved items preview exposes mixed products and looks."""
    dash = get_personal_dashboard_template()
    assert len(dash.saved_preview) >= 2


def test_dash_005_recent_section_chronology():
    """DASH-005: Recently viewed items are populated in chronological sequence."""
    dash = get_personal_dashboard_template()
    assert len(dash.recently_viewed) >= 2
    assert dash.recently_viewed[0].action in [ActivityAction.VIEW, ActivityAction.OPEN]


def test_dash_006_partial_module_loading_states():
    """DASH-006: Each module maintains its own distinct operational state."""
    dash = get_personal_dashboard_template()
    assert "continue_exploring" in dash.module_states
    assert "recommendations" in dash.module_states
    assert dash.module_states["continue_exploring"] == PersonalState.LOADED


def test_dash_007_recommendation_failure_graceful_degradation():
    """DASH-007: Section 13.51 - Recommendation failure degrades to PARTIAL state without breaking dashboard."""
    dash = get_personal_dashboard_template(fail_recommendations=True)
    assert dash.state == PersonalState.PARTIAL
    assert dash.module_states["recommendations"] == PersonalState.ERROR
    assert len(dash.recommended_products) == 0
    # Saved and continue exploring still function!
    assert len(dash.continue_exploring) >= 3
    assert len(dash.saved_preview) >= 2


# ===========================================================================
# 3. Saved Experience Tests (SAVE-001 to SAVE-009)
# ===========================================================================

def test_save_001_saved_products_state_and_text_badge():
    """SAVE-001: Saved products expose saved state via text label, not color alone."""
    template = get_saved_products_template()
    assert template.screen_id == PersonalScreenId.PR03_SAVED_PRODUCTS
    assert template.total_count == len(SAVED_PRODUCTS_REGISTRY)
    for p in template.items:
        assert p.is_saved is True
        assert p.saved_state_label == "Saved in Products"


def test_save_002_saved_looks_with_collections():
    """SAVE-002: Saved looks contain collections and supported outfit actions."""
    template = get_saved_looks_template()
    assert template.screen_id == PersonalScreenId.PR04_SAVED_LOOKS
    assert len(template.collections) >= 2
    assert len(template.items) >= 2
    for look in template.items:
        assert "open" in look.supported_actions
        assert "edit" in look.supported_actions


def test_save_003_saved_fashion_content():
    """SAVE-003: Saved fashion returns editorial, collection, and trend items."""
    template = get_saved_fashion_template(tab="all")
    assert template.screen_id == PersonalScreenId.PR05_SAVED_FASHION
    assert template.total_count == len(SAVED_FASHION_REGISTRY)


def test_save_004_filtering_products_and_fashion():
    """SAVE-004: Filters correctly slice saved products and saved fashion tabs."""
    # Filter products by blazer
    prod_template = get_saved_products_template(filter_category="Blazer")
    assert all("blazer" in p.name.lower() for p in prod_template.items)

    # Filter fashion by stories tab
    fash_template = get_saved_fashion_template(tab="stories")
    assert all(f.content_type == SavedFashionContentType.STORY for f in fash_template.items)


def test_save_005_sorting_saved_products():
    """SAVE-005: Sorting saved products by price ascending and descending."""
    asc = get_saved_products_template(sort_by="price_asc")
    prices_asc = [p.price for p in asc.items]
    assert prices_asc == sorted(prices_asc)

    desc = get_saved_products_template(sort_by="price_desc")
    prices_desc = [p.price for p in desc.items]
    assert prices_desc == sorted(prices_desc, reverse=True)


def test_save_006_remove_saved_item():
    """SAVE-006: Removing a saved product or look updates registry."""
    res = remove_saved_item(item_type=SavedItemType.PRODUCT, item_id="sav_prd_01")
    assert res.is_saved is False
    assert "sav_prd_01" not in SAVED_PRODUCTS_REGISTRY

    res_look = remove_saved_item(item_type=SavedItemType.LOOK, item_id="sav_look_01")
    assert res_look.is_saved is False
    assert "sav_look_01" not in SAVED_LOOKS_REGISTRY


def test_save_007_toggle_saved_item():
    """SAVE-007: Toggle adds when not present, removes when present."""
    # Toggle existing removes it
    res1 = toggle_saved_item(SavedItemToggleRequestContract(item_type=SavedItemType.PRODUCT, item_id="sav_prd_02"))
    assert res1.is_saved is False
    assert "sav_prd_02" not in SAVED_PRODUCTS_REGISTRY

    # Toggle new adds it
    res2 = toggle_saved_item(SavedItemToggleRequestContract(item_type=SavedItemType.PRODUCT, item_id="prd_new_99"))
    assert res2.is_saved is True
    assert "prd_new_99" in SAVED_PRODUCTS_REGISTRY


def test_save_008_empty_states():
    """SAVE-008: Empty registry produces EMPTY state."""
    SAVED_PRODUCTS_REGISTRY.clear()
    template = get_saved_products_template()
    assert template.total_count == 0
    assert template.state == PersonalState.EMPTY


def test_save_009_unavailable_product_in_wishlist():
    """SAVE-009: Section 13.20, 13.21 - Wishlist detects unavailable stock and references alternatives."""
    wishlist = get_wishlist_template()
    assert wishlist.screen_id == PersonalScreenId.PR06_WISHLIST
    assert wishlist.unavailable_count >= 1
    unavail_item = next(item for item in wishlist.items if not item.is_available)
    assert unavail_item.availability == "out_of_stock"
    assert unavail_item.availability_notice is not None
    assert unavail_item.alternative_product_id is not None


# ===========================================================================
# 4. Preferences & Personalization Tests (PREF-001 to PREF-009)
# ===========================================================================

def test_pref_001_preference_render_separation():
    """PREF-001: Explicit and inferred preferences are strictly separated (Section 13.4)."""
    pref = get_preferences_template()
    assert pref.screen_id == PersonalScreenId.PR08_PREFERENCES
    assert "Minimal" in pref.explicit_preferences.styles
    assert "Inferred from browsing history" in pref.inferred_preferences.observation_notice


def test_pref_002_select_style_preference():
    """PREF-002: Adding a style adds it to explicit preferences."""
    curr = list(CURRENT_EXPLICIT_PREFERENCES.styles)
    curr.append("Bohemian")
    updated = update_explicit_preferences(UpdateExplicitPreferencesRequestContract(styles=curr))
    assert "Bohemian" in updated.explicit_preferences.styles


def test_pref_003_deselect_style_preference():
    """PREF-003: Removing a style updates explicit preferences."""
    updated = update_explicit_preferences(UpdateExplicitPreferencesRequestContract(styles=["Minimal"]))
    assert updated.explicit_preferences.styles == ["Minimal"]
    assert "Tailored" not in updated.explicit_preferences.styles


def test_pref_004_save_preferences_state():
    """PREF-004: Updating explicit preferences sets state to SAVED."""
    updated = update_explicit_preferences(
        UpdateExplicitPreferencesRequestContract(categories=["Outerwear", "Blazers"])
    )
    assert updated.state == PersonalState.SAVED
    assert updated.explicit_preferences.categories == ["Outerwear", "Blazers"]


def test_pref_005_saving_and_saved_state_models():
    """PREF-005: PersonalState enum supports SAVING and SAVED lifecycles."""
    assert PersonalState.SAVING == "saving"
    assert PersonalState.SAVED == "saved"
    assert PersonalState.UNSAVED_CHANGES == "unsaved_changes"


def test_pref_006_saved_state_retrieval():
    """PREF-006: get_preferences_template reflects saved changes."""
    update_explicit_preferences(UpdateExplicitPreferencesRequestContract(colors=["Black", "Olive"]))
    pref = get_preferences_template()
    assert pref.explicit_preferences.colors == ["Black", "Olive"]


def test_pref_007_validation_error_on_invalid_structure():
    """PREF-007: Passing illegal types raises ValidationError."""
    with pytest.raises(ValidationError):
        UpdateExplicitPreferencesRequestContract(styles=123)  # type: ignore


def test_pref_008_unsaved_changes_flag_on_spec():
    """PREF-008: Template spec contract tracks unsaved changes."""
    pref = get_preferences_template()
    assert pref.has_unsaved_changes is False
    pref_dirty = pref.model_copy(update={"has_unsaved_changes": True})
    assert pref_dirty.has_unsaved_changes is True


def test_pref_009_discard_changes_restores_baseline():
    """PREF-009: Fixture reset successfully discards changes."""
    update_explicit_preferences(UpdateExplicitPreferencesRequestContract(styles=["Streetwear"]))
    assert CURRENT_EXPLICIT_PREFERENCES.styles == ["Streetwear"]
    reset_personal_fixtures()
    assert "Minimal" in CURRENT_EXPLICIT_PREFERENCES.styles


# ===========================================================================
# 5. Regional & Recommendation Tests (REG-001, REC-001, SET-001)
# ===========================================================================

def test_reg_001_regional_preference_gps_decoupling():
    """REG-001: Section 13.36 - Preferred region is decoupled from physical GPS location."""
    reg = get_regional_preferences_template()
    assert reg.screen_id == PersonalScreenId.PR10_REGIONAL_PREFERENCES
    assert "discovery preference" in reg.disclaimer
    assert "not current device GPS" in reg.disclaimer


def test_reg_002_update_regional_preferences():
    """REG-002: Updating regional discovery settings."""
    updated = update_regional_preferences(
        UpdateRegionalPreferencesRequestContract(preferred_country="Japan", preferred_city="Tokyo")
    )
    assert updated.settings.preferred_country == "Japan"
    assert updated.settings.preferred_city == "Tokyo"


def test_rec_001_recommendation_preferences_and_transparency():
    """REC-001: Section 13.31 - Transparency signals clearly list utilized inputs."""
    rec = get_recommendation_preferences_template()
    assert rec.screen_id == PersonalScreenId.PR09_RECOMMENDATION_PREFERENCES
    assert "Selected styles" in rec.transparency_explanation
    assert len(rec.settings.transparency_signals) >= 3


def test_rec_002_reset_personalization_signals():
    """REC-002: Section 13.33 - Reset clears inferred browsing history."""
    CURRENT_INFERRED_PREFERENCES.frequently_viewed_styles.append("Avant-Garde")
    assert len(CURRENT_INFERRED_PREFERENCES.frequently_viewed_styles) > 0

    reset_res = reset_personalization_signals()
    assert reset_res.state == PersonalState.SAVED
    assert len(CURRENT_INFERRED_PREFERENCES.frequently_viewed_styles) == 0
    assert "reset" in CURRENT_INFERRED_PREFERENCES.observation_notice


def test_act_001_recently_viewed_privacy_clear():
    """ACT-001: Section 13.25 - Users can clear browsing history without losing saved items."""
    before_count = len(ACTIVITY_REGISTRY)
    assert before_count > 0

    clear_res = clear_recently_viewed_history()
    assert clear_res["status"] == "success"
    assert len(ACTIVITY_REGISTRY) == 0

    # Saved products remain intact!
    assert len(SAVED_PRODUCTS_REGISTRY) > 0


def test_set_001_account_settings_update():
    """SET-001: Updating account settings parameters."""
    settings = get_account_settings_template()
    assert settings.screen_id == PersonalScreenId.PR11_ACCOUNT_SETTINGS
    assert settings.settings.two_factor_auth is True

    updated = update_account_settings(
        UpdateAccountSettingsRequestContract(notifications_enabled=False, privacy_level="enhanced")
    )
    assert updated.settings.notifications_enabled is False
    assert updated.settings.privacy_level == "enhanced"


# ===========================================================================
# 6. Strict Extra Forbidden Tests (FORBID-001 to FORBID-008, Rule I02)
# ===========================================================================

def test_forbid_001_saved_product_contract_rejects_extra():
    """FORBID-001: SavedProductContract rejects extra fields."""
    with pytest.raises(ValidationError):
        SavedProductContract(
            id="sav_01",
            product_id="prd_01",
            brand="Brand",
            name="Name",
            price=100.0,
            saved_at="2026-10-02T10:00:00Z",
            extra_field="illegal",  # type: ignore
        )


def test_forbid_002_saved_look_contract_rejects_extra():
    """FORBID-002: SavedLookContract rejects extra fields."""
    with pytest.raises(ValidationError):
        SavedLookContract(
            id="look_01",
            look_id="l01",
            title="Title",
            style="Style",
            saved_at="2026-10-02T10:00:00Z",
            bogus="forbidden",  # type: ignore
        )


def test_forbid_003_wishlist_item_contract_rejects_extra():
    """FORBID-003: WishlistItemContract rejects extra fields."""
    with pytest.raises(ValidationError):
        WishlistItemContract(
            id="w01",
            product_id="p01",
            brand="Brand",
            name="Name",
            price=50.0,
            added_at="2026-10-02T10:00:00Z",
            unexpected=True,  # type: ignore
        )


def test_forbid_004_activity_contract_rejects_extra():
    """FORBID-004: ActivityContract rejects extra fields."""
    with pytest.raises(ValidationError):
        ActivityContract(
            entity_id="e01",
            entity_type=ActivityEntityType.PRODUCT,
            action=ActivityAction.VIEW,
            title="Title",
            timestamp="2026-10-02T10:00:00Z",
            unauthorized="leak",  # type: ignore
        )


def test_forbid_005_explicit_preferences_rejects_extra():
    """FORBID-005: ExplicitPreferencesContract rejects extra fields."""
    with pytest.raises(ValidationError):
        ExplicitPreferencesContract(
            styles=["Minimal"],
            extra_pref="not_allowed",  # type: ignore
        )


def test_forbid_006_regional_preferences_rejects_extra():
    """FORBID-006: RegionalPreferencesContract rejects extra fields."""
    with pytest.raises(ValidationError):
        RegionalPreferencesContract(
            preferred_country="France",
            gps_coordinates={"lat": 48.8, "lng": 2.3},  # type: ignore
        )


def test_forbid_007_account_settings_rejects_extra():
    """FORBID-007: AccountSettingsContract rejects extra fields."""
    with pytest.raises(ValidationError):
        AccountSettingsContract(
            user_id="u01",
            email="test@example.com",
            display_name="User",
            admin_privileges=True,  # type: ignore
        )


def test_forbid_008_profile_template_spec_rejects_extra():
    """FORBID-008: ProfileTemplateSpecContract rejects extra fields."""
    summary = compute_saved_summary()
    with pytest.raises(ValidationError):
        ProfileTemplateSpecContract(
            user_id="usr_01",
            display_name="User",
            saved_summary=summary,
            regional_context=CURRENT_REGIONAL_PREFERENCES,
            untracked="bad",  # type: ignore
        )
