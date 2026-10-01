"""Unit tests for FashXStudio Component Framework — Phase 05.

Validates Level 1 (Primitives) and Level 2 (Core UI) component specifications,
catalog completeness, WCAG accessibility criteria, design token mappings,
and Pydantic v2 contract enforcement (extra="forbid").
"""

import pytest
from schemas.visual.components import (
    BadgeSpecContract,
    BadgeVariant,
    ButtonSpecContract,
    ButtonVariant,
    CardSpecContract,
    CardVariant,
    ComponentCatalogContract,
    ComponentSize,
    ComponentTaxonomy,
    FormFieldSpecContract,
    InputSpecContract,
    InputType,
    ModalSpecContract,
    RatingSpecContract,
    SegmentedControlOptionContract,
    SegmentedControlSpecContract,
    SkeletonShape,
    SkeletonSpecContract,
    TypographyRole,
    TypographySpecContract,
)
from api.app.visual.components_service import (
    get_component_catalog,
    get_component_definition,
    validate_component_props,
)


# ---------------------------------------------------------------------------
# 1. Catalog Completeness & Taxonomy
# ---------------------------------------------------------------------------

def test_component_catalog_contains_primitives_and_core_ui() -> None:
    """Catalog contains both Level 1 Primitives and Level 2 Core UI components."""
    catalog = get_component_catalog()
    assert isinstance(catalog, ComponentCatalogContract)
    assert len(catalog.primitives) >= 7
    assert len(catalog.core_ui) >= 6
    assert catalog.total_components >= 13


def test_primitive_components_taxonomy() -> None:
    """All primitive components have LEVEL_1_PRIMITIVE taxonomy."""
    catalog = get_component_catalog()
    for comp in catalog.primitives:
        assert comp.taxonomy == ComponentTaxonomy.LEVEL_1_PRIMITIVE
        assert len(comp.available_variants) > 0
        assert len(comp.design_tokens_used) > 0
        assert len(comp.wcag_criteria) > 0


def test_core_ui_components_taxonomy() -> None:
    """All core UI components have LEVEL_2_CORE_UI taxonomy."""
    catalog = get_component_catalog()
    for comp in catalog.core_ui:
        assert comp.taxonomy == ComponentTaxonomy.LEVEL_2_CORE_UI
        assert len(comp.available_variants) > 0
        assert len(comp.design_tokens_used) > 0
        assert len(comp.wcag_criteria) > 0


def test_find_component_case_insensitive() -> None:
    """Catalog finds components regardless of case."""
    catalog = get_component_catalog()
    assert catalog.find_component("button") is not None
    assert catalog.find_component("BUTTON") is not None
    assert catalog.find_component("Card") is not None
    assert catalog.find_component("nonexistent") is None


# ---------------------------------------------------------------------------
# 2. Button Spec Contract
# ---------------------------------------------------------------------------

def test_button_spec_defaults_and_wcag_target() -> None:
    """Button defaults to primary MD and enforces >= 44px min touch target."""
    button = ButtonSpecContract(label="Try On")
    assert button.variant == ButtonVariant.PRIMARY
    assert button.size == ComponentSize.MD
    assert button.min_touch_target_px >= 44
    assert button.is_loading is False
    assert button.is_disabled is False


def test_button_spec_variants() -> None:
    """Button supports all 5 designated variants."""
    for variant in ButtonVariant:
        btn = ButtonSpecContract(label="Action", variant=variant)
        assert btn.variant == variant


def test_button_spec_rejects_extra_fields() -> None:
    """Button spec strictly forbids undeclared fields (extra='forbid')."""
    with pytest.raises(Exception):
        ButtonSpecContract(label="Submit", custom_arbitrary_field=True)  # type: ignore


# ---------------------------------------------------------------------------
# 3. Input Spec Contract
# ---------------------------------------------------------------------------

def test_input_spec_defaults() -> None:
    """Input defaults to text type with clear button enabled."""
    inp = InputSpecContract(label="Search Styles", placeholder="Denim, Leather...")
    assert inp.input_type == InputType.TEXT
    assert inp.show_clear_button is True
    assert inp.is_disabled is False
    assert inp.is_required is False


def test_input_spec_error_state() -> None:
    """Input correctly carries error text for accessibility alerting."""
    inp = InputSpecContract(label="Email", error_text="Invalid fashion account email")
    assert inp.error_text == "Invalid fashion account email"


# ---------------------------------------------------------------------------
# 4. Badge Spec Contract
# ---------------------------------------------------------------------------

def test_badge_spec_variants() -> None:
    """Badge supports 8 semantic color variants and pill shaping."""
    for variant in BadgeVariant:
        badge = BadgeSpecContract(label="Trending", variant=variant)
        assert badge.variant == variant
        assert badge.is_pill is True


# ---------------------------------------------------------------------------
# 5. Typography Spec Contract
# ---------------------------------------------------------------------------

def test_typography_spec_roles() -> None:
    """Typography supports 15 type scale hierarchy roles."""
    for role in TypographyRole:
        typ = TypographySpecContract(role=role, text="FashXStudio")
        assert typ.role == role
        assert typ.align == "left"


# ---------------------------------------------------------------------------
# 6. Skeleton Spec Contract
# ---------------------------------------------------------------------------

def test_skeleton_spec_shapes() -> None:
    """Skeleton supports rectangle, rounded, circle, and text shapes."""
    for shape in SkeletonShape:
        skel = SkeletonSpecContract(shape=shape, width=120, height=40)
        assert skel.shape == shape
        assert skel.is_animated is True


# ---------------------------------------------------------------------------
# 7. Card Spec Contract
# ---------------------------------------------------------------------------

def test_card_spec_elevations_and_variants() -> None:
    """Card supports elevations 0-5 and elevated/outlined/filled variants."""
    for el in range(6):
        card = CardSpecContract(elevation=el, variant=CardVariant.ELEVATED)
        assert card.elevation == el

    for v in CardVariant:
        card = CardSpecContract(variant=v)
        assert card.variant == v


def test_card_spec_elevation_bounds() -> None:
    """Card rejects elevation outside 0-5."""
    with pytest.raises(Exception):
        CardSpecContract(elevation=6)


# ---------------------------------------------------------------------------
# 8. Modal & Rating Spec Contracts
# ---------------------------------------------------------------------------

def test_modal_spec_accessibility() -> None:
    """Modal enforces scrim, focus trap, and dialog accessibility role."""
    modal = ModalSpecContract(title="Select Size")
    assert modal.has_scrim is True
    assert modal.has_focus_trap is True
    assert modal.accessibility_role == "dialog"


def test_rating_spec_bounds() -> None:
    """Rating enforces value between 0.0 and 5.0."""
    rating = RatingSpecContract(value=4.5, allow_half=True)
    assert rating.value == 4.5

    with pytest.raises(Exception):
        RatingSpecContract(value=5.5)

    with pytest.raises(Exception):
        RatingSpecContract(value=-0.5)


# ---------------------------------------------------------------------------
# 9. SegmentedControl & FormField Spec Contracts
# ---------------------------------------------------------------------------

def test_segmented_control_spec() -> None:
    """SegmentedControl requires at least 2 options and tracks selected_id."""
    opts = [
        SegmentedControlOptionContract(id="men", label="Men"),
        SegmentedControlOptionContract(id="women", label="Women"),
    ]
    seg = SegmentedControlSpecContract(options=opts, selected_id="women")
    assert len(seg.options) == 2
    assert seg.selected_id == "women"


def test_form_field_spec() -> None:
    """FormField tracks required flag and error state."""
    field = FormFieldSpecContract(
        field_id="size-field",
        label="Size",
        is_required=True,
        state="error",
        error_text="Please select a garment size",
    )
    assert field.is_required is True
    assert field.state == "error"


# ---------------------------------------------------------------------------
# 10. Runtime Prop Validation Engine
# ---------------------------------------------------------------------------

def test_validate_component_props_valid_button() -> None:
    """validate_component_props validates valid Button props."""
    report = validate_component_props("Button", {"label": "Confirm Outfit", "variant": "primary"})
    assert report.is_valid is True
    assert len(report.errors) == 0
    assert report.validated_props["label"] == "Confirm Outfit"


def test_validate_component_props_invalid_missing_required() -> None:
    """validate_component_props rejects Button missing required label."""
    report = validate_component_props("Button", {"variant": "primary"})
    assert report.is_valid is False
    assert len(report.errors) > 0


def test_validate_component_props_rejects_extra_fields() -> None:
    """validate_component_props rejects undeclared props via extra='forbid'."""
    report = validate_component_props(
        "Button", {"label": "Submit", "non_existent_prop": 123}
    )
    assert report.is_valid is False
    assert len(report.errors) > 0


def test_validate_component_props_unrecognized_component() -> None:
    """validate_component_props returns error for unrecognized component."""
    report = validate_component_props("FakeWidget", {"label": "Test"})
    assert report.is_valid is False
    assert "not recognized" in report.errors[0]
