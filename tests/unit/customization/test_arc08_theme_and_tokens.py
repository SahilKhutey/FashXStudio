import copy

import pytest

from app.modules.customization.application.services.theme_resolver import get_theme_resolver
from app.modules.customization.infrastructure.theme_registry import (
    ThemeNotFoundError,
    UnsupportedThemeVersionError,
    get_theme_registry,
)
from app.modules.customization.tokens.validator import (
    validate_color,
    validate_font_family,
    validate_spacing,
    validate_token_overrides,
)

BASE_CONFIG = {
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
        "settings": {"columns": 2, "density": "comfortable"},
    },
    "components": [],
}


def test_arc08_t001_load_valid_theme():
    registry = get_theme_registry()
    theme = registry.get_theme("theme-minimal")
    assert theme["id"] == "theme-minimal"
    assert theme["name"] == "Minimal"
    assert theme["status"] == "active"
    assert "tokens" in theme


def test_arc08_t002_load_unknown_theme():
    registry = get_theme_registry()
    with pytest.raises(ThemeNotFoundError) as exc_info:
        registry.get_theme("theme-nonexistent")
    assert "theme-nonexistent" in str(exc_info.value)


def test_arc08_t003_load_unsupported_theme_version():
    registry = get_theme_registry()
    with pytest.raises(UnsupportedThemeVersionError) as exc_info:
        registry.get_theme("theme-minimal", version="99.9.9")
    assert "99.9.9" in str(exc_info.value)


def test_arc08_t004_use_valid_hex_color():
    assert validate_color("#ff0000") is True
    assert validate_color("#18181b") is True
    assert validate_color("#abc") is True


def test_arc08_t005_use_malformed_color():
    assert validate_color("red") is False
    assert validate_color("#gggggg") is False
    assert validate_color("not-a-color") is False


def test_arc08_t006_use_unsupported_token_path():
    overrides = {"unsupported_category": {"foo": "bar"}}
    is_valid, errors = validate_token_overrides(overrides)
    assert is_valid is False
    assert any("Unsupported token path" in e for e in errors)


def test_arc08_t007_use_arbitrary_css_expression():
    overrides = {"color": {"brand": {"primary": "expression(alert(1))"}}}
    is_valid, errors = validate_token_overrides(overrides)
    assert is_valid is False
    assert any("Arbitrary CSS expression rejected" in e for e in errors)

    overrides2 = {"color": {"brand": {"primary": "url(javascript:alert(1))"}}}
    is_valid2, errors2 = validate_token_overrides(overrides2)
    assert is_valid2 is False


def test_arc08_t008_use_unsupported_font_family():
    assert validate_font_family("Inter") is True
    assert validate_font_family("Merriweather") is True
    assert validate_font_family("Comic Sans MS") is False
    assert validate_font_family("<script>") is False


def test_arc08_t009_use_invalid_spacing_value():
    assert validate_spacing("1rem") is True
    assert validate_spacing("16px") is True
    assert validate_spacing("0") is True
    assert validate_spacing("auto") is False
    assert validate_spacing("100vh") is False


def test_arc08_t010_resolve_theme_defaults():
    resolver = get_theme_resolver()
    resolved = resolver.resolve(BASE_CONFIG)
    assert resolved["theme_id"] == "theme-minimal"
    # theme-minimal has brand.primary = #18181b
    assert resolved["tokens"]["color"]["brand"]["primary"] == "#18181b"
    assert "--mm-color-brand-primary" in resolved["css_variables"]


def test_arc08_t011_apply_restaurant_override():
    resolver = get_theme_resolver()
    cfg = copy.deepcopy(BASE_CONFIG)
    cfg["theme"]["overrides"] = {
        "color": {
            "brand": {
                "primary": "#2563eb"
            }
        }
    }
    resolved = resolver.resolve(cfg)
    assert resolved["tokens"]["color"]["brand"]["primary"] == "#2563eb"
    assert resolved["css_variables"]["--mm-color-brand-primary"] == "#2563eb"


def test_arc08_t012_reset_override():
    resolver = get_theme_resolver()
    cfg = copy.deepcopy(BASE_CONFIG)
    # When override is null or omitted, base theme value is restored
    cfg["theme"]["overrides"] = {
        "color": {
            "brand": {
                "primary": None
            }
        }
    }
    resolved = resolver.resolve(cfg)
    # Base theme value restored (#18181b)
    assert resolved["tokens"]["color"]["brand"]["primary"] == "#18181b"


def test_arc08_t013_apply_conflicting_override():
    resolver = get_theme_resolver()
    cfg = copy.deepcopy(BASE_CONFIG)
    # Platform default: #18181b, Theme preset: #18181b, Override: #10b981
    cfg["theme"]["overrides"] = {
        "color": {
            "brand": {
                "primary": "#10b981"
            }
        }
    }
    resolved = resolver.resolve(cfg)
    # Priority hierarchy: restaurant override strictly wins over base preset
    assert resolved["tokens"]["color"]["brand"]["primary"] == "#10b981"


def test_arc08_t014_resolve_identical_input_twice():
    resolver = get_theme_resolver()
    cfg = copy.deepcopy(BASE_CONFIG)
    cfg["theme"]["overrides"] = {"color": {"brand": {"primary": "#e11d48"}}}
    res1 = resolver.resolve(cfg)
    res2 = resolver.resolve(cfg)
    assert res1["tokens"] == res2["tokens"]
    assert res1["css_variables"] == res2["css_variables"]
    assert res1["layout_settings"] == res2["layout_settings"]


def test_arc08_t015_resolve_without_mutating_source():
    resolver = get_theme_resolver()
    cfg = copy.deepcopy(BASE_CONFIG)
    cfg["theme"]["overrides"] = {"color": {"brand": {"primary": "#7c3aed"}}}
    cfg_copy = copy.deepcopy(cfg)
    _ = resolver.resolve(cfg)
    assert cfg == cfg_copy
