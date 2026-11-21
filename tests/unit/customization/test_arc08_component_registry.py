import copy

import pytest

from app.modules.customization.application.services.customization_validator import (
    get_customization_validator,
)
from app.modules.customization.infrastructure.component_registry import (
    ComponentNotFoundError,
    InvalidComponentPropertyError,
    InvalidSlotPlacementError,
    MaliciousPayloadError,
    RetiredComponentError,
    get_component_registry,
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


def test_arc08_t026_load_registered_component():
    registry = get_component_registry()
    comp = registry.get_component("restaurant-header")
    assert comp["id"] == "restaurant-header"
    assert comp["category"] == "header"
    assert "property_schema" in comp


def test_arc08_t027_load_unregistered_component():
    registry = get_component_registry()
    with pytest.raises(ComponentNotFoundError) as exc_info:
        registry.get_component("unregistered-widget-999")
    assert "unregistered-widget-999" in str(exc_info.value)


def test_arc08_t028_use_valid_component_properties():
    registry = get_component_registry()
    instance = {
        "id": "hdr-1",
        "component_id": "restaurant-header",
        "slot": "header",
        "order": 1,
        "visible": True,
        "props": {
            "show_logo": True,
            "alignment": "center",
        },
    }
    # Should validate without error
    registry.validate_instance(instance)


def test_arc08_t029_add_unknown_property():
    registry = get_component_registry()
    instance = {
        "id": "hdr-1",
        "component_id": "restaurant-header",
        "slot": "header",
        "order": 1,
        "visible": True,
        "props": {
            "show_logo": True,
            "unsupported_arbitrary_key": "injected",
        },
    }
    with pytest.raises(InvalidComponentPropertyError):
        registry.validate_instance(instance)


def test_arc08_t030_add_component_to_supported_slot():
    registry = get_component_registry()
    instance = {
        "id": "nav-1",
        "component_id": "category-navigation",
        "slot": "navigation",
        "order": 1,
        "visible": True,
        "props": {"style": "pills"},
    }
    registry.validate_instance(instance)


def test_arc08_t031_add_component_to_unsupported_slot():
    registry = get_component_registry()
    # category-navigation cannot be placed in footer
    instance = {
        "id": "nav-1",
        "component_id": "category-navigation",
        "slot": "footer",
        "order": 1,
        "visible": True,
        "props": {"style": "pills"},
    }
    with pytest.raises(InvalidSlotPlacementError) as exc_info:
        registry.validate_instance(instance)
    assert "footer" in str(exc_info.value)


def test_arc08_t032_duplicate_component_instance_id():
    validator = get_customization_validator()
    cfg = copy.deepcopy(BASE_CONFIG)
    cfg["components"] = [
        {
            "id": "duplicate-id",
            "component_id": "restaurant-header",
            "slot": "header",
            "order": 1,
            "visible": True,
            "props": {},
        },
        {
            "id": "duplicate-id",
            "component_id": "restaurant-footer",
            "slot": "footer",
            "order": 2,
            "visible": True,
            "props": {},
        },
    ]
    val_res = validator.validate(cfg)
    assert val_res.is_valid is False
    assert any("Duplicate component instance ID" in e.message for e in val_res.errors)


def test_arc08_t033_use_retired_component():
    registry = get_component_registry()
    # Mock retired component
    registry._components["retired-widget"] = {
        "id": "retired-widget",
        "status": "retired",
        "allowed_slots": ["content"],
        "property_schema": {"type": "object"},
    }
    instance = {
        "id": "ret-1",
        "component_id": "retired-widget",
        "slot": "content",
        "order": 1,
        "visible": True,
        "props": {},
    }
    with pytest.raises(RetiredComponentError):
        registry.validate_instance(instance)


def test_arc08_t034_render_deprecated_compatible_version():
    registry = get_component_registry()
    registry._components["deprecated-widget"] = {
        "id": "deprecated-widget",
        "status": "deprecated",
        "allowed_slots": ["content"],
        "property_schema": {"type": "object"},
    }
    instance = {
        "id": "dep-1",
        "component_id": "deprecated-widget",
        "slot": "content",
        "order": 1,
        "visible": True,
        "props": {},
    }
    # Deprecated components remain valid for rendering backward compatibility
    registry.validate_instance(instance)


def test_arc08_t035_submit_executable_component_payload():
    registry = get_component_registry()
    instance = {
        "id": "xss-1",
        "component_id": "restaurant-header",
        "slot": "header",
        "order": 1,
        "visible": True,
        "props": {
            "show_logo": True,
            "custom_text": "<script>alert('xss')</script>",
        },
    }
    with pytest.raises(MaliciousPayloadError) as exc_info:
        registry.validate_instance(instance)
    assert "Malicious executable script/payload rejected" in str(exc_info.value)
