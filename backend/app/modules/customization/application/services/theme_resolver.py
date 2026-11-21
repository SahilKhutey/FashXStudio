import copy
from datetime import UTC, datetime
from typing import Any

from app.modules.customization.infrastructure.component_registry import get_component_registry
from app.modules.customization.infrastructure.layout_registry import get_layout_registry
from app.modules.customization.infrastructure.theme_registry import get_theme_registry
from app.modules.customization.tokens.css_variables import to_css_variables
from app.modules.customization.tokens.tokens import DEFAULT_DESIGN_TOKENS


def _deep_merge_dict(base: dict[str, Any], overrides: dict[str, Any], allow_null_reset: bool = True) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in overrides.items():
        if value is None and allow_null_reset:
            # If null and exists in base, do not override (reset to base) or remove
            # Reset semantics: restore base value
            continue
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = _deep_merge_dict(result[key], value, allow_null_reset)
        else:
            result[key] = copy.deepcopy(value)
    return result


class ThemeResolver:
    def __init__(self) -> None:
        self.theme_registry = get_theme_registry()
        self.layout_registry = get_layout_registry()
        self.component_registry = get_component_registry()

    def resolve(
        self,
        configuration: dict[str, Any],
        menu_id: str = "default",
        revision: int = 1,
    ) -> dict[str, Any]:
        """
        Pure, deterministic resolver applying the 8-tier hierarchy:
        1. Platform defaults
        2. Theme preset
        3. Restaurant theme overrides
        4. Layout defaults
        5. Layout settings
        6. Component registry defaults
        7. Component instance props
        8. Responsive layout overrides
        Does NOT mutate input configuration.
        """
        # Tier 1: Platform defaults
        resolved_tokens = copy.deepcopy(DEFAULT_DESIGN_TOKENS)

        # Tier 2: Theme preset
        theme_cfg = configuration.get("theme", {})
        theme_id = theme_cfg.get("id", "theme-minimal")
        theme_ver = theme_cfg.get("version", "1.0.0")
        theme_def = self.theme_registry.get_theme(theme_id, theme_ver)
        theme_tokens = theme_def.get("tokens", {})
        resolved_tokens = _deep_merge_dict(resolved_tokens, theme_tokens)

        # Tier 3: Restaurant theme overrides
        overrides = theme_cfg.get("overrides", {})
        resolved_tokens = _deep_merge_dict(resolved_tokens, overrides, allow_null_reset=True)

        # Tier 4: Layout defaults
        layout_cfg = configuration.get("layout", {})
        layout_id = layout_cfg.get("id", "layout-grid")
        layout_ver = layout_cfg.get("version", "1.0.0")
        layout_def = self.layout_registry.get_layout(layout_id, layout_ver)
        resolved_layout_settings = copy.deepcopy(layout_def.get("default_settings", {}))

        # Tier 5: Layout settings
        user_layout_settings = layout_cfg.get("settings", {})
        resolved_layout_settings = _deep_merge_dict(resolved_layout_settings, user_layout_settings)

        # Tier 6 & 7: Component defaults & instances
        components_by_slot: dict[str, list[dict[str, Any]]] = {
            "menu.root": [],
            "header": [],
            "navigation": [],
            "content": [],
            "category.header": [],
            "category.items": [],
            "footer": [],
        }

        raw_components = configuration.get("components", [])
        for comp in raw_components:
            cid = comp.get("component_id")
            cdef = self.component_registry.get_component(cid) if cid else {}
            default_props = cdef.get("default_props", {})
            user_props = comp.get("props", {})

            resolved_props = copy.deepcopy(default_props)
            resolved_props.update(copy.deepcopy(user_props))

            instance_copy = {
                "id": comp.get("id"),
                "component_id": cid,
                "slot": comp.get("slot"),
                "order": comp.get("order", 0),
                "visible": comp.get("visible", True),
                "props": resolved_props,
                "renderer": cdef.get("renderer"),
            }

            slot = comp.get("slot", "content")
            if slot not in components_by_slot:
                components_by_slot[slot] = []
            components_by_slot[slot].append(instance_copy)

        # Sort components within slots by order
        for slot in components_by_slot:
            components_by_slot[slot].sort(key=lambda x: x.get("order", 0))

        # Tier 8: Responsive layout settings
        responsive_profiles = copy.deepcopy(layout_def.get("responsive_profiles", {}))
        user_responsive = layout_cfg.get("responsive", {})
        responsive_profiles = _deep_merge_dict(responsive_profiles, user_responsive)

        # Compute deterministic CSS variables
        css_vars = to_css_variables(resolved_tokens)

        return {
            "menu_id": menu_id,
            "revision": revision,
            "configuration_version": configuration.get("configuration_version", "1.0.0"),
            "schema_version": configuration.get("schema_version", "1.0.0"),
            "theme_id": theme_id,
            "theme_version": theme_ver,
            "layout_id": layout_id,
            "layout_version": layout_ver,
            "tokens": resolved_tokens,
            "css_variables": css_vars,
            "layout_settings": resolved_layout_settings,
            "responsive_profiles": responsive_profiles,
            "components_by_slot": components_by_slot,
            "resolved_at": datetime.now(UTC).isoformat(),
        }


_DEFAULT_THEME_RESOLVER = ThemeResolver()


def get_theme_resolver() -> ThemeResolver:
    return _DEFAULT_THEME_RESOLVER
