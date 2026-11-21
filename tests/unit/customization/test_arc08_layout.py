import copy

import pytest

from app.modules.customization.application.services.customization_validator import (
    get_customization_validator,
)
from app.modules.customization.infrastructure.layout_registry import (
    IncompatibleThemeLayoutError,
    InvalidLayoutSettingsError,
    LayoutNotFoundError,
    get_layout_registry,
)

BASE_CONFIG = {
    "configuration_version": "1.0.0",
    "schema_version": "1.0.0",
    "theme": {"id": "theme-minimal", "version": "1.0.0", "overrides": {}},
    "layout": {
        "id": "layout-grid",
        "version": "1.0.0",
        "settings": {"columns": 2, "density": "comfortable"},
    },
    "components": [],
}


def test_arc08_t016_select_supported_layout():
    registry = get_layout_registry()
    layout = registry.get_layout("layout-grid")
    assert layout["id"] == "layout-grid"
    assert layout["status"] == "active"
    assert "default_settings" in layout


def test_arc08_t017_select_unknown_layout():
    registry = get_layout_registry()
    with pytest.raises(LayoutNotFoundError) as exc_info:
        registry.get_layout("layout-unknown-xyz")
    assert "layout-unknown-xyz" in str(exc_info.value)


def test_arc08_t018_use_unsupported_theme_layout_pair():
    # theme-vibrant is incompatible with layout-editorial
    registry = get_layout_registry()
    with pytest.raises(IncompatibleThemeLayoutError) as exc_info:
        registry.check_theme_layout_compatibility("theme-vibrant", "layout-editorial")
    assert "theme-vibrant" in str(exc_info.value)
    assert "layout-editorial" in str(exc_info.value)


def test_arc08_t019_use_invalid_column_count():
    registry = get_layout_registry()
    with pytest.raises(InvalidLayoutSettingsError) as exc_info:
        registry.validate_layout_settings("layout-grid", {"columns": 10})
    assert "Columns must be between 1 and 6" in str(exc_info.value)


def test_arc08_t020_use_valid_mobile_layout():
    registry = get_layout_registry()
    validated = registry.validate_responsive_settings({"mobile": {"columns": 1}})
    assert validated["mobile"]["columns"] == 1


def test_arc08_t021_omit_mobile_override():
    validator = get_customization_validator()
    cfg = copy.deepcopy(BASE_CONFIG)
    cfg["layout"]["responsive"] = {}  # omitted mobile override
    val_res = validator.validate(cfg)
    assert val_res.is_valid is True


def test_arc08_t022_use_arbitrary_breakpoint():
    validator = get_customization_validator()
    cfg = copy.deepcopy(BASE_CONFIG)
    cfg["layout"]["responsive"] = {"arbitrary_viewport": {"columns": 3}}
    val_res = validator.validate(cfg)
    # Rejection of arbitrary unknown breakpoint properties
    assert val_res.is_valid is False


def test_arc08_t023_use_unsupported_slot():
    validator = get_customization_validator()
    cfg = copy.deepcopy(BASE_CONFIG)
    cfg["components"] = [
        {
            "id": "inst-1",
            "component_id": "restaurant-header",
            "slot": "unsupported.custom.slot",
            "order": 1,
            "visible": True,
            "props": {},
        }
    ]
    val_res = validator.validate(cfg)
    assert val_res.is_valid is False
    assert any("slot" in str(e) for e in val_res.errors)


def test_arc08_t024_switch_list_to_grid():
    validator = get_customization_validator()
    cfg = copy.deepcopy(BASE_CONFIG)
    cfg["layout"]["id"] = "layout-list"
    cfg["components"] = [
        {
            "id": "card-1",
            "component_id": "menu-item-card",
            "slot": "content",
            "order": 1,
            "visible": True,
            "props": {"show_image": True},
        }
    ]
    # Validate in list layout
    val1 = validator.validate(cfg)
    assert val1.is_valid is True

    # Switch to grid layout
    cfg["layout"]["id"] = "layout-grid"
    val2 = validator.validate(cfg)
    assert val2.is_valid is True
    # Menu component content is strictly preserved
    assert len(val2.normalized_configuration["components"]) == 1
    assert val2.normalized_configuration["components"][0]["id"] == "card-1"


def test_arc08_t025_render_narrow_viewport():
    # 320px viewport enforces 1 column
    registry = get_layout_registry()
    val_resp = registry.validate_responsive_settings({"mobileSmall": {"columns": 1}})
    assert val_resp["mobileSmall"]["columns"] == 1

    with pytest.raises(InvalidLayoutSettingsError):
        registry.validate_responsive_settings({"mobileSmall": {"columns": 3}})
