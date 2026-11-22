import copy
from typing import Any

try:
    from contracts.src.loader import load_manifest
except ModuleNotFoundError:
    from packages.contracts.src.loader import load_manifest

from app.modules.customization.application.services.customization_validator import (
    get_customization_validator,
)


class ConfigurationMigrationService:
    def __init__(self) -> None:
        self.manifest = load_manifest("configuration-migrations.json")
        self.validator = get_customization_validator()

    def migrate(self, raw_config: dict[str, Any]) -> dict[str, Any]:
        """
        Migrates old configuration documents to canonical 1.0.0 schema.
        If migration fails or input is invalid, preserves the original.
        """
        source_ver = raw_config.get("schema_version")
        if source_ver == "1.0.0":
            return copy.deepcopy(raw_config)

        if source_ver == "0.9.0":
            migrated = copy.deepcopy(raw_config)
            migrated["schema_version"] = "1.0.0"
            migrated["configuration_version"] = "1.0.0"

            # Transform legacy theme structure if present
            theme = migrated.setdefault("theme", {})
            if "id" not in theme:
                theme["id"] = "theme-minimal"
            if "version" not in theme:
                theme["version"] = "1.0.0"

            overrides = theme.setdefault("overrides", {})
            if "primary_color" in theme:
                color = overrides.setdefault("color", {})
                brand = color.setdefault("brand", {})
                brand["primary"] = theme.pop("primary_color")

            if "background_color" in theme:
                color = overrides.setdefault("color", {})
                surface = color.setdefault("surface", {})
                surface["default"] = theme.pop("background_color")

            layout = migrated.setdefault("layout", {})
            if "id" not in layout:
                layout["id"] = "layout-grid"
            if "version" not in layout:
                layout["version"] = "1.0.0"
            if "settings" not in layout:
                layout["settings"] = {"columns": 2, "density": "comfortable"}

            migrated.setdefault("components", [])

            # Validate the migrated result
            val_res = self.validator.validate(migrated)
            if not val_res.is_valid:
                # Preservation rule: if migration produces invalid result, preserve original
                return copy.deepcopy(raw_config)

            return val_res.normalized_configuration or migrated

        # Unsupported or invalid old version: preserve original
        return copy.deepcopy(raw_config)


_DEFAULT_MIGRATION_SERVICE = ConfigurationMigrationService()


def get_migration_service() -> ConfigurationMigrationService:
    return _DEFAULT_MIGRATION_SERVICE
