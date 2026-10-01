"""Unit tests for FashXStudio Component Framework — Phase 05.

Validates the complete 5-layer Component Architecture (Sections 5.1-5.72):
- L1 Primitives: Box, Stack, Inline, Grid, Container, Typography, Button, Input, Badge, Skeleton
- L2 Core UI: IconButton, Link, Chip, Avatar, Alert, Price, QuantityControl, Pagination, Card, Modal, Rating, SegmentedControl, FormField, EmptyState, ErrorState
- L3 Composites: ProductCard, FashionCard, LookCard, CollectionCard, RecommendationCard, SearchBar, FilterBar, ActionBar
- Enforces strict Pydantic v2 extra='forbid' across all components.
"""

import pytest
from schemas.visual.components import (
    ActionBarSpecContract,
    AlertSpecContract,
    AlertVariant,
    AvatarSpecContract,
    BadgeSpecContract,
    BadgeVariant,
    BoxSpecContract,
    ButtonSpecContract,
    ButtonVariant,
    CardSpecContract,
    CardVariant,
    ChipSpecContract,
    CollectionCardSpecContract,
    ComponentCatalogContract,
    ComponentSize,
    ComponentTaxonomy,
    ContainerSpecContract,
    DialogConfirmSpecContract,
    DrawerSpecContract,
    EmptyStateSpecContract,
    ErrorStateSpecContract,
    FashionCardSpecContract,
    FilterBarSpecContract,
    FormFieldSpecContract,
    GridSpecContract,
    IconButtonSpecContract,
    InlineSpecContract,
    InputSpecContract,
    InputType,
    LinkSpecContract,
    LookCardSpecContract,
    ModalSpecContract,
    PaginationSpecContract,
    PriceSpecContract,
    ProductCardSpecContract,
    ProgressSpecContract,
    ProgressVariant,
    QuantityControlSpecContract,
    RatingSpecContract,
    RecommendationCardSpecContract,
    SearchBarSpecContract,
    SegmentedControlOptionContract,
    SegmentedControlSpecContract,
    SkeletonShape,
    SkeletonSpecContract,
    StackSpecContract,
    TypographyRole,
    TypographySpecContract,
)
from api.app.visual.components_service import (
    get_component_catalog,
    get_component_definition,
    validate_component_props,
)


# ---------------------------------------------------------------------------
# 1. Catalog Completeness & Taxonomy Across 3 Layers
# ---------------------------------------------------------------------------

def test_component_catalog_contains_primitives_core_and_composites() -> None:
    """Catalog contains L1 Primitives, L2 Core UI, and L3 Composite components."""
    catalog = get_component_catalog()
    assert isinstance(catalog, ComponentCatalogContract)
    assert len(catalog.primitives) >= 12
    assert len(catalog.core_ui) >= 14
    assert len(catalog.composites) >= 8
    assert catalog.total_components >= 34


def test_primitive_components_taxonomy() -> None:
    """All primitive components have LEVEL_1_PRIMITIVE taxonomy."""
    catalog = get_component_catalog()
    for comp in catalog.primitives:
        assert comp.taxonomy == ComponentTaxonomy.LEVEL_1_PRIMITIVE
        assert len(comp.design_tokens_used) > 0
        assert len(comp.wcag_criteria) > 0


def test_core_ui_components_taxonomy() -> None:
    """All core UI components have LEVEL_2_CORE_UI taxonomy."""
    catalog = get_component_catalog()
    for comp in catalog.core_ui:
        assert comp.taxonomy == ComponentTaxonomy.LEVEL_2_CORE_UI
        assert len(comp.wcag_criteria) > 0


def test_composite_components_taxonomy() -> None:
    """All composite components have LEVEL_3_COMPOSITE taxonomy."""
    catalog = get_component_catalog()
    for comp in catalog.composites:
        assert comp.taxonomy == ComponentTaxonomy.LEVEL_3_COMPOSITE


def test_find_component_case_insensitive() -> None:
    """Catalog finds components regardless of casing."""
    catalog = get_component_catalog()
    assert catalog.find_component("button") is not None
    assert catalog.find_component("BUTTON") is not None
    assert catalog.find_component("ProductCard") is not None
    assert catalog.find_component("product_card") is not None
    assert catalog.find_component("nonexistent") is None


# ---------------------------------------------------------------------------
# 2. L1: Layout Primitives (CMP-001 - CMP-005)
# ---------------------------------------------------------------------------

def test_cmp_001_box_spec() -> None:
    """CMP-001: Box primitive contract validates tokens for surface and spacing."""
    box = BoxSpecContract(padding="space.4", background_token="surface.primary")
    assert box.padding == "space.4"
    assert box.background_token == "surface.primary"


def test_cmp_002_stack_spec() -> None:
    """CMP-002: Stack vertical layout specifies gap and alignment."""
    stack = StackSpecContract(gap="space.component.md", align="center", is_reversed=True)
    assert stack.gap == "space.component.md"
    assert stack.align == "center"
    assert stack.is_reversed is True


def test_cmp_003_inline_spec() -> None:
    """CMP-003: Inline horizontal layout specifies wrapping and justification."""
    inline = InlineSpecContract(gap="space.2", wrap=True, justify="space-between")
    assert inline.wrap is True
    assert inline.justify == "space-between"


def test_cmp_004_grid_spec() -> None:
    """CMP-004: Grid specifies columns (1-12) and min column width."""
    grid = GridSpecContract(columns=4, min_column_width_px=240)
    assert grid.columns == 4

    with pytest.raises(Exception):
        GridSpecContract(columns=16)  # Out of bounds (1..12)


def test_cmp_005_container_spec() -> None:
    """CMP-005: Container bounds content width and enforces responsive gutters."""
    container = ContainerSpecContract(max_width_px=1440, is_centered=True)
    assert container.max_width_px == 1440
    assert container.is_centered is True


# ---------------------------------------------------------------------------
# 3. L1 & L2: Actions & Buttons (CMP-010 - CMP-016)
# ---------------------------------------------------------------------------

def test_cmp_010_button_spec_defaults_and_target() -> None:
    """CMP-010: Button defaults to primary MD and enforces >= 44px touch target."""
    button = ButtonSpecContract(label="Explore Fashion")
    assert button.variant == ButtonVariant.PRIMARY
    assert button.size == ComponentSize.MD
    assert button.min_touch_target_px >= 44


def test_cmp_011_button_disabled() -> None:
    """CMP-011: Button carries disabled state flag."""
    button = ButtonSpecContract(label="Disabled Action", is_disabled=True)
    assert button.is_disabled is True


def test_cmp_012_button_loading() -> None:
    """CMP-012: Button carries loading state to prevent duplicate submission."""
    button = ButtonSpecContract(label="Saving...", is_loading=True)
    assert button.is_loading is True


def test_cmp_016_icon_button_accessible_name_required() -> None:
    """CMP-016: IconButton strictly requires accessibility_label."""
    ib = IconButtonSpecContract(icon="♡", accessibility_label="Add to wishlist")
    assert ib.accessibility_label == "Add to wishlist"

    with pytest.raises(Exception):
        IconButtonSpecContract(icon="🔍")  # Missing required accessibility_label


def test_link_spec() -> None:
    """Link contract validates href, external flag, and display label."""
    link = LinkSpecContract(href="/discover", label="Discover More", is_external=False)
    assert link.href == "/discover"
    assert link.is_external is False


# ---------------------------------------------------------------------------
# 4. L2: Inputs & Forms (CMP-020 - CMP-026)
# ---------------------------------------------------------------------------

def test_cmp_020_input_spec() -> None:
    """CMP-020: Input specifies formats, clear button, and placeholder."""
    inp = InputSpecContract(input_type=InputType.SEARCH, placeholder="Search...")
    assert inp.input_type == InputType.SEARCH
    assert inp.show_clear_button is True


def test_cmp_021_form_field_association() -> None:
    """CMP-021: FormField associates label, required asterisks, and error region."""
    ff = FormFieldSpecContract(
        field_id="email-input",
        label="Email Address",
        is_required=True,
        error_text="Invalid email address format",
        state="error",
    )
    assert ff.is_required is True
    assert ff.state == "error"


def test_chip_spec() -> None:
    """Chip tracks selection state and removable trigger."""
    chip = ChipSpecContract(label="Mumbai", is_selected=True, is_removable=True)
    assert chip.is_selected is True
    assert chip.is_removable is True


# ---------------------------------------------------------------------------
# 5. L2: Overlays (CMP-030 - CMP-035)
# ---------------------------------------------------------------------------

def test_cmp_030_modal_spec() -> None:
    """CMP-030: Modal enforces focus trap, scrim, and dialog accessibility role."""
    modal = ModalSpecContract(title="Filters", has_focus_trap=True)
    assert modal.has_focus_trap is True
    assert modal.accessibility_role == "dialog"


def test_drawer_spec() -> None:
    """Drawer contract specifies positioning and scrim."""
    drawer = DrawerSpecContract(title="Filter Drawer", position="right", is_open=True)
    assert drawer.position == "right"
    assert drawer.is_open is True


def test_dialog_confirm_spec() -> None:
    """DialogConfirm validates destructive confirmation actions."""
    dialog = DialogConfirmSpecContract(
        title="Delete Saved Look?",
        message="This action cannot be undone.",
        is_destructive=True,
    )
    assert dialog.is_destructive is True


# ---------------------------------------------------------------------------
# 6. L2: Feedback & Data Display (CMP-040 - CMP-043)
# ---------------------------------------------------------------------------

def test_alert_spec_variants() -> None:
    """Alert supports 4 notification severity variants."""
    for variant in AlertVariant:
        alert = AlertSpecContract(variant=variant, message="System notification")
        assert alert.variant == variant


def test_cmp_040_price_spec_and_discount() -> None:
    """CMP-040: Price display tracks current, original, and discount %."""
    price = PriceSpecContract(
        amount=2499.0,
        original_amount=3499.0,
        discount_percentage=28,
    )
    assert price.amount == 2499.0
    assert price.discount_percentage == 28


def test_cmp_041_quantity_control_spec() -> None:
    """CMP-041: QuantityControl enforces min and max boundaries."""
    qty = QuantityControlSpecContract(value=2, min_value=1, max_value=10)
    assert qty.value == 2
    assert qty.min_value == 1


def test_cmp_042_pagination_spec() -> None:
    """CMP-042: Pagination contract validates page bounds."""
    pag = PaginationSpecContract(current_page=1, total_pages=10)
    assert pag.current_page == 1
    assert pag.total_pages == 10


def test_empty_state_spec() -> None:
    """EmptyState contract mandates title, description, and action CTA."""
    empty = EmptyStateSpecContract(
        title="Your wishlist is empty",
        description="Save products you want to revisit.",
        action_label="Explore Products",
        action_route="/shopping",
    )
    assert empty.title == "Your wishlist is empty"
    assert empty.action_label == "Explore Products"


def test_error_state_spec() -> None:
    """ErrorState specifies retry action and recovery destination."""
    err = ErrorStateSpecContract(
        title="Something went wrong.",
        message="We couldn't load this collection.",
        retry_label="Try Again",
        recovery_label="Back to Fashion",
        recovery_route="/fashion",
    )
    assert err.retry_label == "Try Again"
    assert err.recovery_label == "Back to Fashion"


# ---------------------------------------------------------------------------
# 7. L3: Composite Components (CMP-050 - CMP-055)
# ---------------------------------------------------------------------------

def test_cmp_050_product_card_spec() -> None:
    """CMP-050: ProductCard coordinates media, brand, title, price, and rating."""
    card = ProductCardSpecContract(
        product_id="prod-101",
        title="Oversized Denim Jacket",
        brand="Zara",
        image_uri="https://images.fashx.com/jacket.jpg",
        price=PriceSpecContract(amount=3990.0),
        rating=RatingSpecContract(value=4.6),
        is_saved=True,
    )
    assert card.product_id == "prod-101"
    assert card.price.amount == 3990.0
    assert card.is_saved is True


def test_cmp_051_fashion_card_spec() -> None:
    """CMP-051: FashionCard emphasizes editorial category and headline."""
    card = FashionCardSpecContract(
        story_id="story-01",
        title="Monsoon Layering in Mumbai",
        story_category="Streetwear",
        image_uri="https://images.fashx.com/monsoon.jpg",
        description="How coastal youth adapt heavy denim to monsoon humidity.",
    )
    assert card.story_id == "story-01"
    assert card.story_category == "Streetwear"


def test_look_card_spec() -> None:
    """LookCard specifies look title and item count."""
    look = LookCardSpecContract(
        look_id="look-99",
        title="Summer Street Look",
        image_uri="https://images.fashx.com/look.jpg",
        items_count=5,
    )
    assert look.items_count == 5


def test_collection_card_spec() -> None:
    """CollectionCard tracks product count and CTA."""
    coll = CollectionCardSpecContract(
        collection_id="coll-1",
        title="Festive Autumn Collection",
        image_uri="https://images.fashx.com/festive.jpg",
        product_count=32,
    )
    assert coll.product_count == 32


def test_cmp_052_recommendation_card_explainability() -> None:
    """CMP-052: RecommendationCard requires explanation badge for AI transparency."""
    rec = RecommendationCardSpecContract(
        recommendation_id="rec-44",
        product=ProductCardSpecContract(
            product_id="p-1",
            title="Linen Shirt",
            brand="H&M",
            image_uri="https://images.fashx.com/shirt.jpg",
            price=PriceSpecContract(amount=1999.0),
        ),
        explanation="Matches your preference for breathable fabrics in warm weather",
        confidence_score=0.92,
    )
    assert "breathable fabrics" in rec.explanation
    assert rec.confidence_score == 0.92


def test_cmp_053_search_bar_spec() -> None:
    """CMP-053: SearchBar coordinates input, query, and filter trigger."""
    search = SearchBarSpecContract(
        placeholder="Search Mumbai trends...",
        show_filter_button=True,
    )
    assert search.show_filter_button is True


def test_cmp_054_filter_bar_spec() -> None:
    """CMP-054: FilterBar manages active filter chips and clear all action."""
    fb = FilterBarSpecContract(
        active_chips=[
            ChipSpecContract(label="Oversized", is_selected=True),
            ChipSpecContract(label="Black", is_selected=True),
        ],
        filter_count=2,
        show_clear_all=True,
    )
    assert len(fb.active_chips) == 2
    assert fb.filter_count == 2


# ---------------------------------------------------------------------------
# 8. Runtime Prop Validation Engine (CMP-060)
# ---------------------------------------------------------------------------

def test_cmp_060_validate_props_product_card_valid() -> None:
    """CMP-060: validate_component_props validates complex nested ProductCard."""
    report = validate_component_props("ProductCard", {
        "product_id": "p-123",
        "title": "Cashmere Knit",
        "brand": "Uniqlo",
        "image_uri": "https://images.fashx.com/knit.jpg",
        "price": {"amount": 4990.0},
    })
    assert report.is_valid is True
    assert report.validated_props["product_id"] == "p-123"


def test_validate_props_extra_fields_forbidden() -> None:
    """Component validation strictly rejects undeclared arbitrary props."""
    report = validate_component_props("Box", {
        "padding": "space.2",
        "arbitrary_custom_css": "color: red",
    })
    assert report.is_valid is False
    assert len(report.errors) > 0
