"""Unit tests for Outfit / Styling / Fashion Experience System — Phase 10.

Verifies:
- STYLE-001 to STYLE-010: ST01 Style Home, ST02 Outfit Builder, Slot Model & Builder State Machine
- STYLE-011 to STYLE-020: Slot Operations (Add, Replace, Remove, Reset, Completeness & Pricing Engine)
- STYLE-021 to STYLE-030: ST03 Look Builder, ST04 Mix & Match Matrix & Instant Swapping
- STYLE-031 to STYLE-040: ST05 Explainable Style Recommendations & ST06 Outfit Preview
- STYLE-041 to STYLE-050: ST07 Outfit Detail, Commerce Availability Validation & Cart Handoff
- STYLE-051 to STYLE-056: ST08 Saved Looks Management & ST09 Style Preferences Customization
- Extra fields forbidden across all Styling contracts (Constitution Rule I02).
"""

import pytest
from pydantic import ValidationError
from schemas.visual.styling import (
    AddSlotItemRequestContract,
    BuilderState,
    CandidateItemContract,
    LookBuilderTemplateSpecContract,
    MixMatchContract,
    MixMatchTemplateSpecContract,
    OutfitContract,
    OutfitDetailTemplateSpecContract,
    OutfitItemContract,
    OutfitPreviewTemplateSpecContract,
    OutfitSlotContract,
    OutfitSource,
    ReplaceSlotItemRequestContract,
    SavedLookContract,
    SavedLooksTemplateSpecContract,
    ShopOutfitAvailabilityContract,
    SlotCategory,
    SlotState,
    StyleHomeTemplateSpecContract,
    StylePreferenceContract,
    StylePreferencesTemplateSpecContract,
    StyleRecommendationTemplateSpecContract,
    StylingScreenId,
)
from fashx.visual.styling_service import (
    INITIAL_OUTFIT,
    SAMPLE_OUTFIT_ITEMS,
    add_item_to_outfit,
    delete_saved_look,
    duplicate_saved_look,
    get_look_builder_template,
    get_mix_match_template,
    get_outfit_builder_template,
    get_outfit_detail_template,
    get_outfit_preview_template,
    get_saved_looks_template,
    get_style_home_template,
    get_style_preferences_template,
    get_style_recommendation_template,
    remove_item_from_outfit,
    replace_item_in_outfit,
    reset_outfit_slots,
    reset_styling_fixtures,
    save_outfit_as_look,
    update_style_preferences,
    validate_outfit_for_shopping,
)


@pytest.fixture(autouse=True)
def restore_styling_fixtures() -> None:
    """Reset outfit registry and preferences before each test to guarantee state isolation."""
    reset_styling_fixtures()


# ---------------------------------------------------------------------------
# STYLE-001 to STYLE-010: ST01 Style Home & ST02 Outfit Builder Canvas
# ---------------------------------------------------------------------------

def test_style_001_to_005_style_home_template() -> None:
    """STYLE-001 to STYLE-005: ST01 Style Home delivers featured style, trending styles, and look feeds."""
    home = get_style_home_template()
    assert home.screen_id == StylingScreenId.ST01_STYLE_HOME
    assert home.featured_style.id == "style-streetwear"
    assert home.featured_style.title == "Contemporary Streetwear"
    assert len(home.popular_styles) >= 1
    assert len(home.recommended_looks) >= 1
    assert len(home.saved_looks_preview) >= 1
    assert home.saved_looks_preview[0].name == "Minimal Summer Linen"


def test_style_006_to_010_outfit_builder_canvas_and_slots() -> None:
    """STYLE-006 to STYLE-010: ST02 Outfit Builder initializes slots with defined categories and initial state."""
    builder = get_outfit_builder_template(INITIAL_OUTFIT.id)
    assert builder.screen_id == StylingScreenId.ST02_OUTFIT_BUILDER
    outfit = builder.outfit
    assert outfit.id == INITIAL_OUTFIT.id
    assert outfit.name == "Monsoon Contemporary Layering"
    assert outfit.style_name == "Contemporary Streetwear"
    assert outfit.source == OutfitSource.MANUAL
    assert len(outfit.slots) >= 5

    # Verify standard slot categories
    categories = [s.category for s in outfit.slots]
    assert SlotCategory.OUTERWEAR in categories
    assert SlotCategory.TOP in categories
    assert SlotCategory.BOTTOM in categories
    assert SlotCategory.FOOTWEAR in categories


# ---------------------------------------------------------------------------
# STYLE-011 to STYLE-020: Slot Operations & Pricing / Completeness Engine
# ---------------------------------------------------------------------------

def test_style_011_to_015_slot_mutations() -> None:
    """STYLE-011 to STYLE-015: Add, replace, remove, and reset slot operations update outfit state deterministically."""
    # Reset outfit slots
    reset_outfit = reset_outfit_slots(INITIAL_OUTFIT.id)
    assert reset_outfit.total_price == 0.0
    assert reset_outfit.is_complete is False
    for slot in reset_outfit.slots:
        assert slot.item is None
        assert slot.state == SlotState.EMPTY

    # Add item to 'slot-top'
    req_add = AddSlotItemRequestContract(
        slot_id="slot-top",
        product_id="prod-linen-02",
        selected_variants={"color": "sand", "size": "L"},
    )
    after_add = add_item_to_outfit(INITIAL_OUTFIT.id, req_add)
    top_slot = next(s for s in after_add.slots if s.id == "slot-top")
    assert top_slot.item is not None
    assert top_slot.item.product_id == "prod-linen-02"
    assert top_slot.item.title == "Relaxed Camp Collar Linen Shirt"
    assert top_slot.item.price == 2499.0
    assert top_slot.state == SlotState.FILLED
    assert after_add.total_price == 2499.0
    assert after_add.is_complete is False

    # Replace item in 'slot-top'
    req_replace = ReplaceSlotItemRequestContract(
        slot_id="slot-top",
        new_product_id="prod-denim-01",
        selected_variants={"color": "raw_indigo", "size": "M"},
    )
    after_replace = replace_item_in_outfit(INITIAL_OUTFIT.id, req_replace)
    top_slot_replaced = next(s for s in after_replace.slots if s.id == "slot-top")
    assert top_slot_replaced.item is not None
    assert top_slot_replaced.item.product_id == "prod-denim-01"
    assert top_slot_replaced.item.price == 4999.0
    assert after_replace.total_price == 4999.0

    # Remove item from 'slot-top'
    after_remove = remove_item_from_outfit(INITIAL_OUTFIT.id, "slot-top")
    top_slot_removed = next(s for s in after_remove.slots if s.id == "slot-top")
    assert top_slot_removed.item is None
    assert top_slot_removed.state == SlotState.EMPTY
    assert after_remove.total_price == 0.0


def test_style_016_to_020_completeness_and_pricing_calculation() -> None:
    """STYLE-016 to STYLE-020: Completeness is true when all required slots are filled; total price is accurate."""
    reset_outfit_slots(INITIAL_OUTFIT.id)

    # Add required slots: top, bottom, footwear
    add_item_to_outfit(
        INITIAL_OUTFIT.id,
        AddSlotItemRequestContract(slot_id="slot-top", product_id="prod-linen-02"),
    )
    add_item_to_outfit(
        INITIAL_OUTFIT.id,
        AddSlotItemRequestContract(slot_id="slot-bottom", product_id="prod-trouser-03"),
    )
    completed_outfit = add_item_to_outfit(
        INITIAL_OUTFIT.id,
        AddSlotItemRequestContract(slot_id="slot-footwear", product_id="prod-derby-04"),
    )

    # Top (2499) + Bottom (3299) + Footwear (5999) = 11797.0
    assert completed_outfit.total_price == 11797.0
    assert completed_outfit.is_complete is True
    reset_styling_fixtures()


# ---------------------------------------------------------------------------
# STYLE-021 to STYLE-030: ST03 Look Builder & ST04 Mix & Match Matrix
# ---------------------------------------------------------------------------

def test_style_021_to_025_look_builder_template() -> None:
    """STYLE-021 to STYLE-025: ST03 Look Builder presents moodboard canvas and visual narrative tags."""
    look_b = get_look_builder_template("look-mumbai-01")
    assert look_b.screen_id == StylingScreenId.ST03_LOOK_BUILDER
    assert look_b.look_id == "look-mumbai-01"
    assert "Contemporary Streetwear" in look_b.style_tags
    assert len(look_b.visual_items) >= 2
    assert look_b.state == BuilderState.EDITING


def test_style_026_to_030_mix_match_matrix_and_swapping() -> None:
    """STYLE-026 to STYLE-030: ST04 Mix & Match generates candidate alternatives for each active slot."""
    mix_match = get_mix_match_template(INITIAL_OUTFIT.id)
    assert mix_match.screen_id == StylingScreenId.ST04_MIX_MATCH
    matrix = mix_match.matrix
    assert matrix.outfit_id == INITIAL_OUTFIT.id
    assert len(matrix.candidates_by_slot) >= 4

    top_candidates = next(c for c in matrix.candidates_by_slot if c.slot_id == "slot-top")
    assert top_candidates.category == SlotCategory.TOP
    assert len(top_candidates.products) >= 2

    # Swap with candidate product
    candidate_prod = top_candidates.products[0]
    swapped = replace_item_in_outfit(
        INITIAL_OUTFIT.id,
        ReplaceSlotItemRequestContract(
            slot_id="slot-top",
            new_product_id=candidate_prod.product_id,
        ),
    )
    swapped_slot = next(s for s in swapped.slots if s.id == "slot-top")
    assert swapped_slot.item.product_id == candidate_prod.product_id


# ---------------------------------------------------------------------------
# STYLE-031 to STYLE-040: ST05 Style Recommendations & ST06 Outfit Preview
# ---------------------------------------------------------------------------

def test_style_031_to_035_style_recommendations() -> None:
    """STYLE-031 to STYLE-035: ST05 Style Recommendation delivers transparent rationale and matching pieces."""
    recs = get_style_recommendation_template("user-1")
    assert recs.screen_id == StylingScreenId.ST05_STYLE_RECOMMENDATION
    assert recs.recommended_style_name == "Relaxed Minimalist"
    assert "preferences" in recs.explanation.lower()
    assert len(recs.recommended_looks) >= 1
    assert len(recs.recommended_products) >= 1


def test_style_036_to_040_outfit_preview() -> None:
    """STYLE-036 to STYLE-040: ST06 Outfit Preview provides clean read-only summary with accurate counts."""
    preview = get_outfit_preview_template(INITIAL_OUTFIT.id)
    assert preview.screen_id == StylingScreenId.ST06_OUTFIT_PREVIEW
    assert preview.outfit.id == INITIAL_OUTFIT.id
    assert preview.item_count >= 1
    assert preview.total_price >= 0.0


# ---------------------------------------------------------------------------
# STYLE-041 to STYLE-050: ST07 Outfit Detail & Commerce Availability
# ---------------------------------------------------------------------------

def test_style_041_to_045_outfit_detail() -> None:
    """STYLE-041 to STYLE-045: ST07 Outfit Detail renders constituent products, similar outfits, and shoppable links."""
    detail = get_outfit_detail_template(INITIAL_OUTFIT.id)
    assert detail.screen_id == StylingScreenId.ST07_OUTFIT_DETAIL
    assert detail.outfit.name == "Monsoon Contemporary Layering"
    assert len(detail.constituent_items) >= 1
    assert detail.availability.can_proceed_to_cart is True


def test_style_046_to_050_commerce_availability_validation() -> None:
    """STYLE-046 to STYLE-050: Pre-purchase validation accurately checks item availability and total cost."""
    avail = validate_outfit_for_shopping(INITIAL_OUTFIT.id)
    assert avail.outfit_id == INITIAL_OUTFIT.id
    assert avail.total_items >= 1
    assert avail.available_items == avail.total_items
    assert len(avail.unavailable_product_ids) == 0
    assert avail.can_proceed_to_cart is True
    assert avail.total_price > 0.0


# ---------------------------------------------------------------------------
# STYLE-051 to STYLE-056: ST08 Saved Looks & ST09 Style Preferences
# ---------------------------------------------------------------------------

def test_style_051_to_053_saved_looks_management() -> None:
    """STYLE-051 to STYLE-053: ST08 Saved looks allows listing, filtering, duplicating, and deleting looks."""
    # List saved looks
    saved = get_saved_looks_template(user_id="user-1", filter_tag="all")
    assert saved.screen_id == StylingScreenId.ST08_SAVED_LOOKS
    assert saved.total_saved >= 1
    first_look = saved.saved_looks[0]

    # Duplicate look
    cloned = duplicate_saved_look(first_look.id)
    assert "(Copy)" in cloned.name
    assert len(cloned.items) == len(first_look.items)

    # Delete cloned look
    del_res = delete_saved_look(cloned.id)
    assert del_res is True

    # Attempt delete nonexistent look
    del_nonexistent = delete_saved_look("look-non-existent-999")
    assert del_nonexistent is False


def test_style_054_to_056_style_preferences() -> None:
    """STYLE-054 to STYLE-056: ST09 Style Preferences permits customized aesthetic and budget updates."""
    prefs = get_style_preferences_template(user_id="user-1")
    assert prefs.screen_id == StylingScreenId.ST09_STYLE_PREFERENCES
    assert "Contemporary Streetwear" in prefs.preferences.preferred_styles
    assert "Relaxed Boxy" in prefs.preferences.preferred_fits

    # Update preferences
    updated_contract = StylePreferenceContract(
        user_id="user-1",
        preferred_styles=["Minimalism", "Streetwear", "Cyberpunk"],
        preferred_fits=["Oversized", "Tailored"],
        preferred_colors=["Black", "Charcoal", "Indigo"],
        preferred_materials=["Silk", "Cashmere", "Selvedge Denim"],
        budget_tier="luxury",
    )
    result = update_style_preferences("user-1", updated_contract)
    assert result.budget_tier == "luxury"
    assert "Cyberpunk" in result.preferred_styles
    assert "Selvedge Denim" in result.preferred_materials


# ---------------------------------------------------------------------------
# Constitution Rule I02: Extra Fields Forbidden Validation
# ---------------------------------------------------------------------------

def test_styling_extra_fields_forbidden() -> None:
    """Enforce Constitution Rule I02: extra fields forbidden across all styling contracts."""
    with pytest.raises(ValidationError):
        OutfitItemContract(
            slot_id="slot-top",
            product_id="prod-01",
            title="Tee",
            brand="Brand",
            image_uri="https://images.fashx.com/tee.jpg",
            price=999.0,
            invalid_extra_field="rejected",  # type: ignore
        )

    with pytest.raises(ValidationError):
        OutfitSlotContract(
            id="slot-err",
            category=SlotCategory.TOP,
            name="Top",
            position=0,
            forbidden_attr=True,  # type: ignore
        )

    with pytest.raises(ValidationError):
        OutfitContract(
            id="outfit-err",
            name="Error Outfit",
            style_id="style-1",
            style_name="Style",
            unsupported_key=123,  # type: ignore
        )

    with pytest.raises(ValidationError):
        SavedLookContract(
            id="saved-err",
            user_id="user-1",
            name="Saved",
            style_name="Style",
            created_at="2026-10-02",
            updated_at="2026-10-02",
            extra_payload="fail",  # type: ignore
        )

    with pytest.raises(ValidationError):
        ShopOutfitAvailabilityContract(
            outfit_id="outfit-01",
            total_items=3,
            available_items=3,
            bonus_discount="fail",  # type: ignore
        )
