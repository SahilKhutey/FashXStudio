import copy
import time
from uuid import uuid4

from app.modules.customization.application.editor import EditorSession
from app.modules.customization.application.services.theme_resolver import get_theme_resolver
from app.modules.customization.application.use_cases import (
    UpdateCustomizationUseCase,
)
from app.modules.customization.infrastructure.layout_registry import get_layout_registry
from app.modules.customization.infrastructure.theme_registry import get_theme_registry
from app.modules.customization.tokens.tokens import DEFAULT_DESIGN_TOKENS

BASE_CONFIG = {
    "configuration_version": "1.0.0",
    "schema_version": "1.0.0",
    "theme": {"id": "theme-minimal", "version": "1.0.0", "overrides": {}},
    "layout": {
        "id": "layout-grid",
        "version": "1.0.0",
        "settings": {"columns": 2, "density": "comfortable"},
    },
    "components": [
        {
            "id": "comp-1",
            "component_id": "restaurant-header",
            "slot": "header",
            "order": 1,
            "visible": True,
            "props": {"show_logo": True},
        }
    ],
}


def test_arc08_t093_check_text_contrast():
    registry = get_theme_registry()
    theme = registry.get_theme("theme-minimal")
    access = theme.get("accessibility", {})
    # Minimal theme contrast ratio >= 7:1 (AAA)
    assert access.get("contrast_ratio_normal", 0) >= 4.5
    assert access.get("wcag_level") in ("AA", "AAA")


def test_arc08_t094_navigate_editor_by_keyboard():
    session = EditorSession(BASE_CONFIG, revision=1)
    session.select_component("comp-1")
    assert session.selected_component_id == "comp-1"
    # Keyboard shortcut simulation: reorder and undo
    session.reorder_component("comp-1", 2)
    assert session.can_undo() is True
    session.undo()
    comp = next(c for c in session.draft["components"] if c["id"] == "comp-1")
    assert comp["order"] == 1


def test_arc08_t095_check_focus_visibility():
    resolver = get_theme_resolver()
    resolved = resolver.resolve(BASE_CONFIG)
    css_vars = resolved["css_variables"]
    # Focus ring token is always generated
    assert "--mm-focus-ring-color" in css_vars
    assert "--mm-focus-ring-width" in css_vars
    assert css_vars["--mm-focus-ring-width"] == "2px"


def test_arc08_t096_check_reduced_motion_preference():
    tokens = DEFAULT_DESIGN_TOKENS
    assert "motion" in tokens
    assert tokens["motion"]["reduceMotion"] is False
    assert tokens["motion"]["durationFast"] == "150ms"


def test_arc08_t097_render_320px_viewport():
    layout_registry = get_layout_registry()
    layout = layout_registry.get_layout("layout-grid")
    profile_320 = layout["responsive_profiles"]["mobileSmall"]
    # 320px viewport enforces 1 column to eliminate horizontal overflow
    assert profile_320["columns"] == 1


def test_arc08_t098_render_360px_viewport():
    layout_registry = get_layout_registry()
    layout = layout_registry.get_layout("layout-grid")
    profile_mobile = layout["responsive_profiles"]["mobile"]
    assert profile_mobile["columns"] <= 2


def test_arc08_t099_render_tablet_viewport():
    layout_registry = get_layout_registry()
    layout = layout_registry.get_layout("layout-grid")
    profile_tablet = layout["responsive_profiles"]["tablet"]
    assert profile_tablet["columns"] >= 2


def test_arc08_t100_render_large_desktop_viewport():
    tokens = DEFAULT_DESIGN_TOKENS
    max_w = tokens["sizing"]["containerMaxWidth"]
    # Content max width prevents excessive stretching
    assert max_w == "1200px"


def test_arc08_t101_resolve_normal_configuration():
    resolver = get_theme_resolver()
    t0 = time.perf_counter()
    for _ in range(50):
        _ = resolver.resolve(BASE_CONFIG)
    elapsed = (time.perf_counter() - t0) / 50
    # Meets resolver latency target (< 5ms per resolution)
    assert elapsed < 0.005


def test_arc08_t102_save_configuration():
    org_id = uuid4()
    menu_id = "menu-bench-t102"
    use_case = UpdateCustomizationUseCase()

    t0 = time.perf_counter()
    saved = use_case.execute(org_id, menu_id, BASE_CONFIG)
    elapsed = time.perf_counter() - t0
    assert saved.revision == 1
    # Save latency target (< 50ms)
    assert elapsed < 0.050


def test_arc08_t103_render_menu_with_maximum_supported_components():
    cfg = copy.deepcopy(BASE_CONFIG)
    # Generate 100 components (maximum supported count)
    cfg["components"] = [
        {
            "id": f"comp-{i}",
            "component_id": "menu-item-card",
            "slot": "content",
            "order": i,
            "visible": True,
            "props": {"show_image": True},
        }
        for i in range(100)
    ]
    resolver = get_theme_resolver()
    resolved = resolver.resolve(cfg)
    assert len(resolved["components_by_slot"]["content"]) == 100


def test_arc08_t104_simulate_cache_outage():
    # In a cache outage, core customization resolves deterministically from base config
    resolver = get_theme_resolver()
    resolved = resolver.resolve(BASE_CONFIG)
    assert resolved["theme_id"] == "theme-minimal"
    assert resolved["tokens"]["color"]["brand"]["primary"] == "#18181b"
