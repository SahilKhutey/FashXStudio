"""Outfit, Styling & Fashion Experience Domain Service — Phase 10.

Provides domain models, builder state machines, slot managers, mix & match candidate generators,
recommendation adapters, saved looks persistence, and shopping validation (Sections 10.1 - 10.88).
"""

from datetime import datetime, timezone
from typing import Any
from schemas.visual.fashion import (
    FashionContentType,
    VisualContentModel,
)
from schemas.visual.styling import (
    AddSlotItemRequestContract,
    BuilderState,
    CandidateItemContract,
    LookBuilderTemplateSpecContract,
    MixMatchContract,
    MixMatchTemplateSpecContract,
    OutfitBuilderTemplateSpecContract,
    OutfitContract,
    OutfitDetailTemplateSpecContract,
    OutfitItemContract,
    OutfitPreviewTemplateSpecContract,
    OutfitSlotContract,
    OutfitSource,
    ReplaceSlotItemRequestContract,
    SavedLookContract,
    SavedLooksTemplateSpecContract,
    SaveOutfitRequestContract,
    ShopOutfitAvailabilityContract,
    SlotCategory,
    SlotState,
    StyleHomeTemplateSpecContract,
    StylePreferenceContract,
    StylePreferencesTemplateSpecContract,
    StyleRecommendationTemplateSpecContract,
    StylingScreenId,
)
from .fashion_service import (
    SAMPLE_LOOKS,
    SAMPLE_PRODUCTS,
    SAMPLE_STYLES,
    to_visual_content_model,
)


# ---------------------------------------------------------------------------
# Initial Fixtures & In-Memory Stores (Sections 10.3 - 10.6, 10.29, 10.33)
# ---------------------------------------------------------------------------

SAMPLE_OUTFIT_ITEMS: dict[str, OutfitItemContract] = {
    "prod-denim-01": OutfitItemContract(
        slot_id="slot-outerwear",
        product_id="prod-denim-01",
        title="Selvedge Oversized Denim Jacket",
        brand="RawDenim Co.",
        image_uri="https://images.fashx.com/products/denim_jacket_front.jpg",
        price=4999.0,
        original_price=6999.0,
        selected_variants={"color": "raw_indigo", "size": "M"},
        is_available=True,
        quantity=1,
    ),
    "prod-linen-02": OutfitItemContract(
        slot_id="slot-top",
        product_id="prod-linen-02",
        title="Relaxed Camp Collar Linen Shirt",
        brand="Breeze & Loom",
        image_uri="https://images.fashx.com/products/linen_shirt_sand.jpg",
        price=2499.0,
        original_price=None,
        selected_variants={"color": "sand", "size": "L"},
        is_available=True,
        quantity=1,
    ),
    "prod-trouser-03": OutfitItemContract(
        slot_id="slot-bottom",
        product_id="prod-trouser-03",
        title="Pleated Wide-Leg Cotton Trousers",
        brand="Artisan Loom",
        image_uri="https://images.fashx.com/products/trouser_charcoal.jpg",
        price=3299.0,
        original_price=3999.0,
        selected_variants={"color": "charcoal", "size": "32"},
        is_available=True,
        quantity=1,
    ),
    "prod-derby-04": OutfitItemContract(
        slot_id="slot-footwear",
        product_id="prod-derby-04",
        title="Chunky Lug-Sole Leather Derby",
        brand="Kojima Footwear",
        image_uri="https://images.fashx.com/products/derby_black.jpg",
        price=5999.0,
        original_price=None,
        selected_variants={"size": "42"},
        is_available=True,
        quantity=1,
    ),
}

DEFAULT_OUTFIT_SLOTS: list[OutfitSlotContract] = [
    OutfitSlotContract(
        id="slot-top",
        category=SlotCategory.TOP,
        name="Top",
        position=0,
        required=True,
        item=SAMPLE_OUTFIT_ITEMS["prod-linen-02"],
        state=SlotState.FILLED,
    ),
    OutfitSlotContract(
        id="slot-outerwear",
        category=SlotCategory.OUTERWEAR,
        name="Outerwear",
        position=1,
        required=False,
        item=SAMPLE_OUTFIT_ITEMS["prod-denim-01"],
        state=SlotState.FILLED,
    ),
    OutfitSlotContract(
        id="slot-bottom",
        category=SlotCategory.BOTTOM,
        name="Bottom",
        position=2,
        required=True,
        item=SAMPLE_OUTFIT_ITEMS["prod-trouser-03"],
        state=SlotState.FILLED,
    ),
    OutfitSlotContract(
        id="slot-footwear",
        category=SlotCategory.FOOTWEAR,
        name="Footwear",
        position=3,
        required=True,
        item=SAMPLE_OUTFIT_ITEMS["prod-derby-04"],
        state=SlotState.FILLED,
    ),
    OutfitSlotContract(
        id="slot-accessory",
        category=SlotCategory.ACCESSORY,
        name="Accessory",
        position=4,
        required=False,
        item=None,
        state=SlotState.EMPTY,
    ),
]

INITIAL_OUTFIT = OutfitContract(
    id="outfit-monsoon-streetwear-01",
    name="Monsoon Contemporary Layering",
    style_id="style-streetwear",
    style_name="Contemporary Streetwear",
    slots=DEFAULT_OUTFIT_SLOTS,
    hero_image_uri="https://images.fashx.com/outfits/monsoon_layering.jpg",
    source=OutfitSource.MANUAL,
    total_price=16796.0,
    is_complete=True,
    notes="Balanced humidity-resistant textures pairing heavyweight selvedge denim with breathable French flax linen.",
)

# In-memory mutable outfit registry
OUTFITS_REGISTRY: dict[str, OutfitContract] = {
    INITIAL_OUTFIT.id: INITIAL_OUTFIT,
}

# In-memory mutable saved looks
SAVED_LOOKS_REGISTRY: dict[str, SavedLookContract] = {
    "saved-look-01": SavedLookContract(
        id="saved-look-01",
        user_id="user-1",
        name="Minimal Summer Linen",
        style_name="Relaxed Minimalist",
        created_at="2026-09-25T14:30:00Z",
        updated_at="2026-09-25T14:30:00Z",
        items=[SAMPLE_OUTFIT_ITEMS["prod-linen-02"], SAMPLE_OUTFIT_ITEMS["prod-trouser-03"]],
        hero_image_uri="https://images.fashx.com/looks/summer_minimal.jpg",
        is_favorite=True,
        collection_tag="Summer Capsule",
    ),
    "saved-look-02": SavedLookContract(
        id="saved-look-02",
        user_id="user-1",
        name="Monsoon Streetwear Edit",
        style_name="Contemporary Streetwear",
        created_at="2026-09-28T10:15:00Z",
        updated_at="2026-09-28T10:15:00Z",
        items=[SAMPLE_OUTFIT_ITEMS["prod-denim-01"], SAMPLE_OUTFIT_ITEMS["prod-derby-04"]],
        hero_image_uri="https://images.fashx.com/looks/monsoon_edit.jpg",
        is_favorite=False,
        collection_tag="Street Edit",
    ),
}

# In-memory user style preferences
DEFAULT_STYLE_PREFERENCES = StylePreferenceContract(
    user_id="user-1",
    preferred_styles=["Contemporary Streetwear", "Artisanal Handloom", "Relaxed Minimalist"],
    preferred_fits=["Relaxed Boxy", "Drop Shoulder", "Wide Leg"],
    preferred_colors=["Indigo", "Raw Ecru", "Charcoal", "Olive"],
    preferred_materials=["100% French Flax Linen", "Japanese Selvedge Denim", "Organic Cotton"],
    budget_tier="medium-luxury",
)

USER_STYLE_PREFERENCES: dict[str, StylePreferenceContract] = {
    "user-1": StylePreferenceContract(**DEFAULT_STYLE_PREFERENCES.model_dump()),
}


# ---------------------------------------------------------------------------
# ST01: Style Home (Section 10.5 & 10.6)
# ---------------------------------------------------------------------------

def get_style_home_template() -> StyleHomeTemplateSpecContract:
    """Build ST01 Style Home gateway template specification."""
    return StyleHomeTemplateSpecContract(
        screen_id=StylingScreenId.ST01_STYLE_HOME,
        featured_style=to_visual_content_model(SAMPLE_STYLES[0], FashionContentType.STYLE),
        popular_styles=[to_visual_content_model(s, FashionContentType.STYLE) for s in SAMPLE_STYLES],
        recommended_looks=[to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS],
        saved_looks_preview=list(SAVED_LOOKS_REGISTRY.values())[:3],
    )


# ---------------------------------------------------------------------------
# ST02: Outfit Builder & Slot Operations (Section 10.7 - 10.15)
# ---------------------------------------------------------------------------

def get_outfit_builder_template(outfit_id: str | None = None) -> OutfitBuilderTemplateSpecContract:
    """Build ST02 primary interactive outfit workspace template specification."""
    target_id = outfit_id or INITIAL_OUTFIT.id
    outfit = OUTFITS_REGISTRY.get(target_id, INITIAL_OUTFIT)

    return OutfitBuilderTemplateSpecContract(
        screen_id=StylingScreenId.ST02_OUTFIT_BUILDER,
        outfit=outfit,
        active_slot_id=outfit.slots[0].id if outfit.slots else None,
        available_categories=[
            SlotCategory.TOP,
            SlotCategory.BOTTOM,
            SlotCategory.OUTERWEAR,
            SlotCategory.FOOTWEAR,
            SlotCategory.ACCESSORY,
            SlotCategory.BAG,
        ],
        state=BuilderState.EDITING,
    )


def add_item_to_outfit(outfit_id: str, payload: AddSlotItemRequestContract) -> OutfitContract:
    """Add or assign an item to an outfit slot (Section 10.13)."""
    outfit = OUTFITS_REGISTRY.get(outfit_id, INITIAL_OUTFIT)
    if payload.product_id in SAMPLE_OUTFIT_ITEMS:
        item_ref = SAMPLE_OUTFIT_ITEMS[payload.product_id]
        new_item = OutfitItemContract(
            slot_id=payload.slot_id,
            product_id=item_ref.product_id,
            title=item_ref.title,
            brand=item_ref.brand,
            image_uri=item_ref.image_uri,
            price=item_ref.price,
            original_price=item_ref.original_price,
            selected_variants=payload.selected_variants or item_ref.selected_variants,
            is_available=item_ref.is_available,
            quantity=1,
        )
    else:
        matching_prod = next((p for p in SAMPLE_PRODUCTS if p.id == payload.product_id), SAMPLE_PRODUCTS[0])
        new_item = OutfitItemContract(
            slot_id=payload.slot_id,
            product_id=matching_prod.id,
            title=matching_prod.title,
            brand=matching_prod.brand,
            image_uri=matching_prod.primary_image_uri,
            price=matching_prod.price.amount,
            original_price=matching_prod.price.original_amount,
            selected_variants=payload.selected_variants,
            is_available=matching_prod.is_in_stock,
            quantity=1,
        )

    new_slots: list[OutfitSlotContract] = []
    total_price = 0.0
    for slot in outfit.slots:
        if slot.id == payload.slot_id:
            updated_slot = OutfitSlotContract(
                id=slot.id,
                category=slot.category,
                name=slot.name,
                position=slot.position,
                required=slot.required,
                item=new_item,
                state=SlotState.FILLED,
            )
            new_slots.append(updated_slot)
            total_price += new_item.price
        else:
            new_slots.append(slot)
            if slot.item:
                total_price += slot.item.price

    updated_outfit = OutfitContract(
        id=outfit.id,
        name=outfit.name,
        style_id=outfit.style_id,
        style_name=outfit.style_name,
        slots=new_slots,
        hero_image_uri=outfit.hero_image_uri,
        source=outfit.source,
        total_price=total_price,
        is_complete=all(s.item is not None for s in new_slots if s.required),
        notes=outfit.notes,
    )
    OUTFITS_REGISTRY[outfit.id] = updated_outfit
    return updated_outfit


def replace_item_in_outfit(outfit_id: str, payload: ReplaceSlotItemRequestContract) -> OutfitContract:
    """Replace an existing slot item with a new product choice (Section 10.14)."""
    add_req = AddSlotItemRequestContract(
        slot_id=payload.slot_id,
        product_id=payload.new_product_id,
        selected_variants=payload.selected_variants,
    )
    return add_item_to_outfit(outfit_id=outfit_id, payload=add_req)


def remove_item_from_outfit(outfit_id: str, slot_id: str) -> OutfitContract:
    """Remove item from slot, resetting it to empty (Section 10.15)."""
    outfit = OUTFITS_REGISTRY.get(outfit_id, INITIAL_OUTFIT)
    new_slots: list[OutfitSlotContract] = []
    total_price = 0.0

    for slot in outfit.slots:
        if slot.id == slot_id:
            new_slots.append(
                OutfitSlotContract(
                    id=slot.id,
                    category=slot.category,
                    name=slot.name,
                    position=slot.position,
                    required=slot.required,
                    item=None,
                    state=SlotState.EMPTY,
                )
            )
        else:
            new_slots.append(slot)
            if slot.item:
                total_price += slot.item.price

    updated_outfit = OutfitContract(
        id=outfit.id,
        name=outfit.name,
        style_id=outfit.style_id,
        style_name=outfit.style_name,
        slots=new_slots,
        hero_image_uri=outfit.hero_image_uri,
        source=outfit.source,
        total_price=total_price,
        is_complete=all(s.item is not None for s in new_slots if s.required),
        notes=outfit.notes,
    )
    OUTFITS_REGISTRY[outfit.id] = updated_outfit
    return updated_outfit


def reset_outfit_slots(outfit_id: str) -> OutfitContract:
    """Reset all slots in the outfit to empty (Section 10.36, 10.67 STYLE-019)."""
    outfit = OUTFITS_REGISTRY.get(outfit_id, INITIAL_OUTFIT)
    empty_slots = [
        OutfitSlotContract(
            id=slot.id,
            category=slot.category,
            name=slot.name,
            position=slot.position,
            required=slot.required,
            item=None,
            state=SlotState.EMPTY,
        )
        for slot in outfit.slots
    ]

    reset_outfit = OutfitContract(
        id=outfit.id,
        name=outfit.name,
        style_id=outfit.style_id,
        style_name=outfit.style_name,
        slots=empty_slots,
        hero_image_uri=outfit.hero_image_uri,
        source=outfit.source,
        total_price=0.0,
        is_complete=False,
        notes=outfit.notes,
    )
    OUTFITS_REGISTRY[outfit.id] = reset_outfit
    return reset_outfit


# ---------------------------------------------------------------------------
# ST03 & ST04: Look Builder & Mix & Match (Sections 10.16 - 10.19)
# ---------------------------------------------------------------------------

def get_look_builder_template(look_id: str | None = None) -> LookBuilderTemplateSpecContract:
    """Build ST03 creative visual look composition canvas template specification."""
    target_look = next((l for l in SAMPLE_LOOKS if l.id == look_id), SAMPLE_LOOKS[0])
    return LookBuilderTemplateSpecContract(
        screen_id=StylingScreenId.ST03_LOOK_BUILDER,
        look_id=target_look.id,
        title=f"Editorial Composition: {target_look.title}",
        style_tags=["Contemporary Streetwear", "Monsoon Humidity", "Architectural Drape"],
        context_narrative="Compose editorial looks balancing functional silhouette lines with luxury artisanal textiles.",
        visual_items=list(SAMPLE_OUTFIT_ITEMS.values())[:3],
        state=BuilderState.EDITING,
    )


def get_mix_match_template(outfit_id: str | None = None) -> MixMatchTemplateSpecContract:
    """Build ST04 Mix & Match alternative experimentation template specification."""
    target_id = outfit_id or INITIAL_OUTFIT.id
    outfit = OUTFITS_REGISTRY.get(target_id, INITIAL_OUTFIT)
    current_items = [s.item for s in outfit.slots if s.item is not None]

    candidates_by_slot: list[CandidateItemContract] = [
        CandidateItemContract(
            slot_id="slot-top",
            category=SlotCategory.TOP,
            products=[
                SAMPLE_OUTFIT_ITEMS["prod-linen-02"],
                OutfitItemContract(
                    slot_id="slot-top",
                    product_id="prod-tshirt-05",
                    title="Heavyweight Raw Cotton Tee",
                    brand="Artisan Raw",
                    image_uri="https://images.fashx.com/products/raw_tee_white.jpg",
                    price=1899.0,
                    is_available=True,
                ),
            ],
        ),
        CandidateItemContract(
            slot_id="slot-outerwear",
            category=SlotCategory.OUTERWEAR,
            products=[
                SAMPLE_OUTFIT_ITEMS["prod-denim-01"],
                OutfitItemContract(
                    slot_id="slot-outerwear",
                    product_id="prod-blazer-06",
                    title="Unstructured Linen Work Blazer",
                    brand="Breeze & Loom",
                    image_uri="https://images.fashx.com/products/linen_blazer.jpg",
                    price=5499.0,
                    is_available=True,
                ),
            ],
        ),
        CandidateItemContract(
            slot_id="slot-bottom",
            category=SlotCategory.BOTTOM,
            products=[SAMPLE_OUTFIT_ITEMS["prod-trouser-03"]],
        ),
        CandidateItemContract(
            slot_id="slot-footwear",
            category=SlotCategory.FOOTWEAR,
            products=[SAMPLE_OUTFIT_ITEMS["prod-derby-04"]],
        ),
    ]

    return MixMatchTemplateSpecContract(
        screen_id=StylingScreenId.ST04_MIX_MATCH,
        matrix=MixMatchContract(
            outfit_id=outfit.id,
            current_items=current_items,
            candidates_by_slot=candidates_by_slot,
        ),
    )


# ---------------------------------------------------------------------------
# ST05, ST06, ST07: Recommendations, Preview & Detail (Sections 10.20 - 10.28)
# ---------------------------------------------------------------------------

def get_style_recommendation_template(user_id: str = "user-1") -> StyleRecommendationTemplateSpecContract:
    """Build ST05 explainable style recommendations template specification (Section 10.20)."""
    return StyleRecommendationTemplateSpecContract(
        screen_id=StylingScreenId.ST05_STYLE_RECOMMENDATION,
        recommended_style_name="Relaxed Minimalist",
        explanation="Curated based on your explored preferences for French flax linen and boxy Japanese tailoring.",
        recommended_looks=[to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS],
        recommended_products=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS],
    )


def get_outfit_preview_template(outfit_id: str) -> OutfitPreviewTemplateSpecContract:
    """Build ST06 read-only outfit preview template specification (Section 10.23)."""
    outfit = OUTFITS_REGISTRY.get(outfit_id, INITIAL_OUTFIT)
    filled_items = [s.item for s in outfit.slots if s.item is not None]

    return OutfitPreviewTemplateSpecContract(
        screen_id=StylingScreenId.ST06_OUTFIT_PREVIEW,
        outfit=outfit,
        item_count=len(filled_items),
        total_price=outfit.total_price,
    )


def validate_outfit_for_shopping(outfit_id: str) -> ShopOutfitAvailabilityContract:
    """Validate item availability and compute totals before cart handoff (Section 10.28)."""
    outfit = OUTFITS_REGISTRY.get(outfit_id, INITIAL_OUTFIT)
    filled_items = [s.item for s in outfit.slots if s.item is not None]

    available_ids = [i.product_id for i in filled_items if i.is_available]
    unavailable_ids = [i.product_id for i in filled_items if not i.is_available]

    return ShopOutfitAvailabilityContract(
        outfit_id=outfit.id,
        total_items=len(filled_items),
        available_items=len(available_ids),
        available_product_ids=available_ids,
        unavailable_product_ids=unavailable_ids,
        can_proceed_to_cart=len(available_ids) > 0,
        total_price=sum(i.price for i in filled_items if i.is_available),
    )


def get_outfit_detail_template(outfit_id: str) -> OutfitDetailTemplateSpecContract:
    """Build ST07 comprehensive outfit detail template specification (Section 10.25)."""
    outfit = OUTFITS_REGISTRY.get(outfit_id, INITIAL_OUTFIT)
    constituent_items = [s.item for s in outfit.slots if s.item is not None]
    availability = validate_outfit_for_shopping(outfit_id=outfit.id)

    return OutfitDetailTemplateSpecContract(
        screen_id=StylingScreenId.ST07_OUTFIT_DETAIL,
        outfit=outfit,
        constituent_items=constituent_items,
        similar_outfits=[INITIAL_OUTFIT],
        availability=availability,
    )


# ---------------------------------------------------------------------------
# ST08 & ST09: Saved Looks & Preferences (Sections 10.29 - 10.35)
# ---------------------------------------------------------------------------

def get_saved_looks_template(user_id: str = "user-1", filter_tag: str = "all") -> SavedLooksTemplateSpecContract:
    """Build ST08 saved looks archive template specification (Section 10.29)."""
    all_looks = [l for l in SAVED_LOOKS_REGISTRY.values() if l.user_id == user_id]
    if filter_tag == "favorites":
        filtered_looks = [l for l in all_looks if l.is_favorite]
    elif filter_tag != "all":
        filtered_looks = [l for l in all_looks if (l.collection_tag or "").lower() == filter_tag.lower()]
    else:
        filtered_looks = all_looks

    return SavedLooksTemplateSpecContract(
        screen_id=StylingScreenId.ST08_SAVED_LOOKS,
        saved_looks=filtered_looks,
        total_saved=len(filtered_looks),
        active_filter=filter_tag,
    )


def save_outfit_as_look(payload: SaveOutfitRequestContract) -> SavedLookContract:
    """Save an outfit as a persistent saved look (Section 10.31)."""
    outfit = OUTFITS_REGISTRY.get(payload.outfit_id, INITIAL_OUTFIT)
    now_iso = datetime.now(timezone.utc).isoformat()
    new_id = f"saved-{payload.outfit_id}-{len(SAVED_LOOKS_REGISTRY) + 1}"

    saved_look = SavedLookContract(
        id=new_id,
        user_id=payload.user_id,
        name=payload.name,
        style_name=outfit.style_name,
        created_at=now_iso,
        updated_at=now_iso,
        items=[s.item for s in outfit.slots if s.item is not None],
        hero_image_uri=outfit.hero_image_uri,
        is_favorite=False,
        collection_tag=payload.collection_tag,
    )
    SAVED_LOOKS_REGISTRY[saved_look.id] = saved_look
    return saved_look


def duplicate_saved_look(look_id: str, new_name: str | None = None) -> SavedLookContract:
    """Duplicate an existing saved look for rapid experimentation (Section 10.32)."""
    source_look = SAVED_LOOKS_REGISTRY.get(look_id)
    if not source_look:
        source_look = list(SAVED_LOOKS_REGISTRY.values())[0]

    now_iso = datetime.now(timezone.utc).isoformat()
    dup_id = f"{source_look.id}-copy-{len(SAVED_LOOKS_REGISTRY) + 1}"

    duplicated = SavedLookContract(
        id=dup_id,
        user_id=source_look.user_id,
        name=new_name or f"{source_look.name} (Copy)",
        style_name=source_look.style_name,
        created_at=now_iso,
        updated_at=now_iso,
        items=list(source_look.items),
        hero_image_uri=source_look.hero_image_uri,
        is_favorite=source_look.is_favorite,
        collection_tag=source_look.collection_tag,
    )
    SAVED_LOOKS_REGISTRY[duplicated.id] = duplicated
    return duplicated


def delete_saved_look(look_id: str) -> bool:
    """Remove a look from saved looks store (Section 10.30)."""
    if look_id in SAVED_LOOKS_REGISTRY:
        del SAVED_LOOKS_REGISTRY[look_id]
        return True
    return False


def get_style_preferences_template(user_id: str = "user-1") -> StylePreferencesTemplateSpecContract:
    """Build ST09 style preference selector template specification (Section 10.33)."""
    pref = USER_STYLE_PREFERENCES.get(user_id, USER_STYLE_PREFERENCES["user-1"])
    return StylePreferencesTemplateSpecContract(
        screen_id=StylingScreenId.ST09_STYLE_PREFERENCES,
        preferences=pref,
        available_styles=["Contemporary Streetwear", "Artisanal Handloom", "Relaxed Minimalist", "Classic Tailoring", "Bohemian"],
        available_fits=["Relaxed Boxy", "Oversized", "Regular Fit", "Slim Tailored", "Wide Leg"],
        available_colors=["Indigo", "Raw Ecru", "Charcoal", "Olive", "Terracotta", "Bone White"],
        available_materials=["100% French Flax Linen", "Japanese Selvedge Denim", "Organic Cotton", "Chanderi Silk"],
    )


def update_style_preferences(user_id: str, preferences: StylePreferenceContract) -> StylePreferenceContract:
    """Update and persist user style preferences (Section 10.34)."""
    USER_STYLE_PREFERENCES[user_id] = preferences
    return preferences


def reset_styling_fixtures() -> None:
    """Reset in-memory registries to default pristine state for test isolation."""
    USER_STYLE_PREFERENCES["user-1"] = StylePreferenceContract(**DEFAULT_STYLE_PREFERENCES.model_dump())
    OUTFITS_REGISTRY[INITIAL_OUTFIT.id] = OutfitContract(
        id=INITIAL_OUTFIT.id,
        name=INITIAL_OUTFIT.name,
        style_id=INITIAL_OUTFIT.style_id,
        style_name=INITIAL_OUTFIT.style_name,
        slots=[
            OutfitSlotContract(
                id=s.id,
                category=s.category,
                name=s.name,
                position=s.position,
                required=s.required,
                item=OutfitItemContract(**s.item.model_dump()) if s.item else None,
                state=s.state,
            )
            for s in DEFAULT_OUTFIT_SLOTS
        ],
        hero_image_uri=INITIAL_OUTFIT.hero_image_uri,
        source=INITIAL_OUTFIT.source,
        total_price=INITIAL_OUTFIT.total_price,
        is_complete=INITIAL_OUTFIT.is_complete,
        notes=INITIAL_OUTFIT.notes,
    )
