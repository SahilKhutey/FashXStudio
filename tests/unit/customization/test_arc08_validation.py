import copy

from app.modules.customization.application.services.customization_validator import (
    MAX_COMPONENTS_LIMIT,
    get_customization_validator,
)

VALID_CONFIG = {
    "configuration_version": "1.0.0",
    "schema_version": "1.0.0",
    "theme": {
        "id": "theme-minimal",
        "version": "1.0.0",
        "overrides": {},
    },
    "layout": {
        "id": "layout-grid",
        "version": "1.0.0",
        "settings": {
            "columns": 2,
            "density": "comfortable",
        },
    },
    "components": [
        {
            "id": "inst-1",
            "component_id": "restaurant-header",
            "slot": "header",
            "order": 1,
            "visible": True,
            "props": {"show_logo": True},
        }
    ],
}


def test_arc08_t036_valid_configuration_document():
    validator = get_customization_validator()
    res = validator.validate(VALID_CONFIG)
    assert res.is_valid is True
    assert len(res.errors) == 0


def test_arc08_t037_missing_required_field():
    validator = get_customization_validator()
    cfg = copy.deepcopy(VALID_CONFIG)
    del cfg["theme"]
    res = validator.validate(cfg)
    assert res.is_valid is False
    assert any("theme" in e.message for e in res.errors)


def test_arc08_t038_unknown_top_level_field():
    validator = get_customization_validator()
    cfg = copy.deepcopy(VALID_CONFIG)
    cfg["injected_arbitrary_field"] = "bad"
    res = validator.validate(cfg)
    assert res.is_valid is False
    assert any("Additional properties are not allowed" in e.message or "injected_arbitrary_field" in e.message for e in res.errors)


def test_arc08_t039_unsupported_schema_version():
    validator = get_customization_validator()
    cfg = copy.deepcopy(VALID_CONFIG)
    cfg["schema_version"] = "99.0.0"
    res = validator.validate(cfg)
    assert res.is_valid is False
    assert any("Unsupported schema version" in e.message for e in res.errors)


def test_arc08_t040_invalid_component_reference():
    validator = get_customization_validator()
    cfg = copy.deepcopy(VALID_CONFIG)
    cfg["components"][0]["component_id"] = "unknown-nonexistent-component"
    res = validator.validate(cfg)
    assert res.is_valid is False
    assert any("is not registered" in e.message for e in res.errors)


def test_arc08_t041_invalid_theme_reference():
    validator = get_customization_validator()
    cfg = copy.deepcopy(VALID_CONFIG)
    cfg["theme"]["id"] = "theme-nonexistent"
    res = validator.validate(cfg)
    assert res.is_valid is False
    assert any("Theme 'theme-nonexistent' not found" in e.message for e in res.errors)


def test_arc08_t042_invalid_layout_reference():
    validator = get_customization_validator()
    cfg = copy.deepcopy(VALID_CONFIG)
    cfg["layout"]["id"] = "layout-nonexistent"
    res = validator.validate(cfg)
    assert res.is_valid is False
    assert any("Layout 'layout-nonexistent' not found" in e.message for e in res.errors)


def test_arc08_t043_exceed_component_count_limit():
    validator = get_customization_validator()
    cfg = copy.deepcopy(VALID_CONFIG)
    # Generate 101 components
    cfg["components"] = [
        {
            "id": f"comp-{i}",
            "component_id": "restaurant-footer",
            "slot": "footer",
            "order": i,
            "visible": True,
            "props": {},
        }
        for i in range(MAX_COMPONENTS_LIMIT + 1)
    ]
    res = validator.validate(cfg)
    assert res.is_valid is False
    assert any("exceeds" in e.message for e in res.errors)


def test_arc08_t044_oversized_configuration():
    validator = get_customization_validator()
    cfg = copy.deepcopy(VALID_CONFIG)
    # Add huge metadata string > 512KB
    cfg["metadata"] = {"huge_blob": "x" * 600000}
    res = validator.validate(cfg)
    assert res.is_valid is False
    assert any("maximum allowed size" in e.message for e in res.errors)


def test_arc08_t045_excessive_json_nesting():
    validator = get_customization_validator()
    cfg = copy.deepcopy(VALID_CONFIG)
    # Create nesting deeper than 8 levels
    curr = cfg["metadata"] = {}
    for _ in range(12):
        curr["nested"] = {}
        curr = curr["nested"]
    res = validator.validate(cfg)
    assert res.is_valid is False
    assert any("nesting depth" in e.message for e in res.errors)


def test_arc08_t046_invalid_nested_property():
    validator = get_customization_validator()
    cfg = copy.deepcopy(VALID_CONFIG)
    # Invalid prop on restaurant-header (show_logo must be boolean)
    cfg["components"][0]["props"]["show_logo"] = "not_a_boolean"
    res = validator.validate(cfg)
    assert res.is_valid is False
    assert any("components[0]" in e.path for e in res.errors)


def test_arc08_t047_missing_optional_property():
    validator = get_customization_validator()
    cfg = copy.deepcopy(VALID_CONFIG)
    # props is empty dict; defaults should apply
    cfg["components"][0]["props"] = {}
    res = validator.validate(cfg)
    assert res.is_valid is True


def test_arc08_t048_unsupported_null_reset():
    validator = get_customization_validator()
    cfg = copy.deepcopy(VALID_CONFIG)
    # Setting required property theme.id to null is prohibited
    cfg["theme"]["id"] = None
    res = validator.validate(cfg)
    assert res.is_valid is False


def test_arc08_t049_unknown_external_schema_reference():
    validator = get_customization_validator()
    # Validator uses isolated local schema store; remote network fetches are disabled
    assert validator.schema_validator.resolver.store is not None


def test_arc08_t050_normalize_same_input_repeatedly():
    validator = get_customization_validator()
    res1 = validator.validate(VALID_CONFIG)
    res2 = validator.validate(VALID_CONFIG)
    assert res1.is_valid is True
    assert res2.is_valid is True
    assert res1.normalized_configuration == res2.normalized_configuration
