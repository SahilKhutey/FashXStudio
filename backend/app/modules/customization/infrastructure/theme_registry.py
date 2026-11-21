import copy
from typing import Any

from contracts.src.loader import load_manifest


class ThemeNotFoundError(Exception):
    def __init__(self, theme_id: str):
        super().__init__(f"Theme '{theme_id}' not found")
        self.theme_id = theme_id


class UnsupportedThemeVersionError(Exception):
    def __init__(self, theme_id: str, version: str):
        super().__init__(f"Theme '{theme_id}' does not support version '{version}'")
        self.theme_id = theme_id
        self.version = version


class RetiredThemeError(Exception):
    def __init__(self, theme_id: str):
        super().__init__(f"Theme '{theme_id}' is retired and cannot be newly selected")
        self.theme_id = theme_id


class ThemeRegistry:
    def __init__(self) -> None:
        raw = load_manifest("theme-catalogue.json")
        self._themes: dict[str, dict[str, Any]] = {}
        for t in raw.get("themes", []):
            self._themes[t["id"]] = t

    def get_theme(self, theme_id: str, version: str | None = None) -> dict[str, Any]:
        if theme_id not in self._themes:
            raise ThemeNotFoundError(theme_id)

        theme = self._themes[theme_id]
        if version is not None and theme["version"] != version:
            raise UnsupportedThemeVersionError(theme_id, version)

        return copy.deepcopy(theme)

    def list_themes(self, include_retired: bool = False) -> list[dict[str, Any]]:
        results = []
        for theme in self._themes.values():
            if not include_retired and theme.get("status") == "retired":
                continue
            results.append(copy.deepcopy(theme))
        return results

    def validate_theme_selection(self, theme_id: str, version: str | None = None) -> dict[str, Any]:
        theme = self.get_theme(theme_id, version)
        if theme.get("status") == "retired":
            raise RetiredThemeError(theme_id)
        return theme


_DEFAULT_THEME_REGISTRY = ThemeRegistry()


def get_theme_registry() -> ThemeRegistry:
    return _DEFAULT_THEME_REGISTRY
