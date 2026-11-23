import copy
from typing import Any

try:
    from contracts.src.loader import load_manifest
except ModuleNotFoundError:
    from packages.contracts.src.loader import load_manifest


class LayoutNotFoundError(Exception):
    def __init__(self, layout_id: str):
        super().__init__(f"Layout '{layout_id}' not found")
        self.layout_id = layout_id


class IncompatibleThemeLayoutError(Exception):
    def __init__(self, theme_id: str, layout_id: str):
        super().__init__(f"Theme '{theme_id}' is not compatible with layout '{layout_id}'")
        self.theme_id = theme_id
        self.layout_id = layout_id


class InvalidLayoutSettingsError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class LayoutRegistry:
    def __init__(self) -> None:
        raw_layouts = load_manifest("layout-catalogue.json")
        self._layouts: dict[str, dict[str, Any]] = {}
        for l in raw_layouts.get("layouts", []):
            self._layouts[l["id"]] = l

        compat = load_manifest("compatibility-matrix.json")
        self._compat_matrix = compat.get("theme_layout_compatibility", {})
        self._supported_breakpoints = set(compat.get("supported_breakpoints", []))

    def get_layout(self, layout_id: str, version: str | None = None) -> dict[str, Any]:
        if layout_id not in self._layouts:
            raise LayoutNotFoundError(layout_id)

        layout = self._layouts[layout_id]
        if version is not None and layout["version"] != version:
            raise InvalidLayoutSettingsError(f"Layout '{layout_id}' does not support version '{version}'")

        return copy.deepcopy(layout)

    def list_layouts(self) -> list[dict[str, Any]]:
        return [copy.deepcopy(l) for l in self._layouts.values()]

    def check_theme_layout_compatibility(self, theme_id: str, layout_id: str) -> None:
        allowed = self._compat_matrix.get(theme_id)
        if allowed is not None and layout_id not in allowed:
            raise IncompatibleThemeLayoutError(theme_id, layout_id)

    def validate_layout_settings(self, layout_id: str, settings: dict[str, Any]) -> dict[str, Any]:
        layout = self.get_layout(layout_id)
        columns = settings.get("columns", layout["default_settings"].get("columns", 1))
        if not isinstance(columns, int) or columns < 1 or columns > 6:
            raise InvalidLayoutSettingsError(f"Columns must be between 1 and 6, got {columns}")

        density = settings.get("density", layout["default_settings"].get("density", "compact"))
        if density not in ("compact", "comfortable", "spacious"):
            raise InvalidLayoutSettingsError(f"Invalid density: {density}")

        return {
            "columns": columns,
            "density": density,
            "image_position": settings.get("image_position", layout["default_settings"].get("image_position", "top")),
            "category_navigation_style": settings.get("category_navigation_style", layout["default_settings"].get("category_navigation_style", "pills")),
        }

    def validate_responsive_settings(self, responsive: dict[str, Any]) -> dict[str, Any]:
        validated = {}
        for bp_key, bp_settings in responsive.items():
            if not isinstance(bp_settings, dict):
                raise InvalidLayoutSettingsError(f"Breakpoint setting for '{bp_key}' must be an object")

            cols = bp_settings.get("columns")
            if cols is not None:
                if bp_key == "mobileSmall" and cols != 1:
                    raise InvalidLayoutSettingsError("mobileSmall (320px) supports only 1 column")
                if bp_key == "mobile" and (cols < 1 or cols > 2):
                    raise InvalidLayoutSettingsError("mobile (375px) supports maximum 2 columns")
                if cols < 1 or cols > 6:
                    raise InvalidLayoutSettingsError(f"Invalid column count for {bp_key}: {cols}")

            validated[bp_key] = bp_settings
        return validated


_DEFAULT_LAYOUT_REGISTRY = LayoutRegistry()


def get_layout_registry() -> LayoutRegistry:
    return _DEFAULT_LAYOUT_REGISTRY
