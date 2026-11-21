import json
from dataclasses import dataclass, field
from typing import Any

from contracts.src.loader import get_menu_customization_validator

from app.modules.customization.infrastructure.component_registry import (
    ComponentNotFoundError,
    InvalidComponentPropertyError,
    InvalidSlotPlacementError,
    MaliciousPayloadError,
    RetiredComponentError,
    get_component_registry,
)
from app.modules.customization.infrastructure.layout_registry import (
    IncompatibleThemeLayoutError,
    InvalidLayoutSettingsError,
    LayoutNotFoundError,
    get_layout_registry,
)
from app.modules.customization.infrastructure.theme_registry import (
    RetiredThemeError,
    ThemeNotFoundError,
    UnsupportedThemeVersionError,
    get_theme_registry,
)
from app.modules.customization.tokens.validator import validate_token_overrides

MAX_COMPONENTS_LIMIT = 100
MAX_CONFIGURATION_BYTES = 524288  # 512 KB
MAX_NESTING_DEPTH = 8
SUPPORTED_SCHEMA_VERSIONS = {"1.0.0"}


@dataclass
class ValidationIssue:
    path: str
    message: str
    code: str


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    normalized_configuration: dict[str, Any] | None = None


def _get_max_depth(obj: Any, current_depth: int = 1) -> int:
    if isinstance(obj, dict):
        if not obj:
            return current_depth
        return max(_get_max_depth(v, current_depth + 1) for v in obj.values())
    if isinstance(obj, list):
        if not obj:
            return current_depth
        return max(_get_max_depth(v, current_depth + 1) for v in obj)
    return current_depth


class CustomizationValidator:
    def __init__(self) -> None:
        self.schema_validator = get_menu_customization_validator()
        self.theme_registry = get_theme_registry()
        self.layout_registry = get_layout_registry()
        self.component_registry = get_component_registry()

    def validate(self, config: dict[str, Any]) -> ValidationResult:
        errors: list[ValidationIssue] = []
        warnings: list[str] = []

        # 1. Payload size check
        try:
            serialized = json.dumps(config)
            if len(serialized.encode("utf-8")) > MAX_CONFIGURATION_BYTES:
                errors.append(
                    ValidationIssue(
                        path="$",
                        message=f"Configuration exceeds maximum allowed size of {MAX_CONFIGURATION_BYTES} bytes",
                        code="OVERSIZED_CONFIGURATION",
                    )
                )
                return ValidationResult(is_valid=False, errors=errors)
        except Exception as e:
            errors.append(ValidationIssue(path="$", message=f"JSON serialization error: {e}", code="SERIALIZATION_ERROR"))
            return ValidationResult(is_valid=False, errors=errors)

        # 2. Nesting depth check
        depth = _get_max_depth(config)
        if depth > MAX_NESTING_DEPTH:
            errors.append(
                ValidationIssue(
                    path="$",
                    message=f"Configuration nesting depth ({depth}) exceeds limit ({MAX_NESTING_DEPTH})",
                    code="EXCESSIVE_NESTING",
                )
            )
            return ValidationResult(is_valid=False, errors=errors)

        # 3. Schema version check
        schema_ver = config.get("schema_version")
        if schema_ver not in SUPPORTED_SCHEMA_VERSIONS:
            errors.append(
                ValidationIssue(
                    path="schema_version",
                    message=f"Unsupported schema version '{schema_ver}'. Supported: {list(SUPPORTED_SCHEMA_VERSIONS)}",
                    code="UNSUPPORTED_SCHEMA_VERSION",
                )
            )
            return ValidationResult(is_valid=False, errors=errors)

        # 3b. Component count limit check
        components = config.get("components", [])
        if len(components) > MAX_COMPONENTS_LIMIT:
            errors.append(
                ValidationIssue(
                    path="components",
                    message=f"Component count ({len(components)}) exceeds maximum limit ({MAX_COMPONENTS_LIMIT})",
                    code="EXCEED_COMPONENT_LIMIT",
                )
            )
            return ValidationResult(is_valid=False, errors=errors)

        # 4. JSON Schema structural validation
        schema_errors = sorted(self.schema_validator.iter_errors(config), key=lambda e: [str(p) for p in e.path])
        for err in schema_errors:
            # Build path like components[0].props.show_logo
            parts = []
            for p in err.path:
                if isinstance(p, int):
                    parts.append(f"[{p}]")
                else:
                    if parts and not parts[-1].endswith("]"):
                        parts.append(f".{p}")
                    else:
                        parts.append(str(p))
            path_str = "".join(parts) if parts else "$"
            errors.append(
                ValidationIssue(
                    path=path_str,
                    message=err.message,
                    code="SCHEMA_VALIDATION_ERROR",
                )
            )

        if errors:
            return ValidationResult(is_valid=False, errors=errors)

        # 5. Semantic validation: Theme
        theme_cfg = config.get("theme", {})
        theme_id = theme_cfg.get("id")
        theme_ver = theme_cfg.get("version")
        try:
            self.theme_registry.validate_theme_selection(theme_id, theme_ver)
        except (ThemeNotFoundError, UnsupportedThemeVersionError, RetiredThemeError) as e:
            errors.append(ValidationIssue(path="theme.id", message=str(e), code="INVALID_THEME"))

        # 6. Semantic validation: Token Overrides
        overrides = theme_cfg.get("overrides", {})
        if overrides:
            valid_tok, tok_errs = validate_token_overrides(overrides)
            if not valid_tok:
                for te in tok_errs:
                    errors.append(ValidationIssue(path="theme.overrides", message=te, code="INVALID_TOKEN_OVERRIDE"))

        # 7. Semantic validation: Layout
        layout_cfg = config.get("layout", {})
        layout_id = layout_cfg.get("id")
        layout_ver = layout_cfg.get("version")
        try:
            self.layout_registry.get_layout(layout_id, layout_ver)
            if theme_id:
                self.layout_registry.check_theme_layout_compatibility(theme_id, layout_id)
            settings = layout_cfg.get("settings", {})
            if settings:
                self.layout_registry.validate_layout_settings(layout_id, settings)
            responsive = layout_cfg.get("responsive", {})
            if responsive:
                self.layout_registry.validate_responsive_settings(responsive)
        except (LayoutNotFoundError, IncompatibleThemeLayoutError, InvalidLayoutSettingsError) as e:
            errors.append(ValidationIssue(path="layout.id", message=str(e), code="INVALID_LAYOUT"))

        # 8. Semantic validation: Components
        components = config.get("components", [])
        if len(components) > MAX_COMPONENTS_LIMIT:
            errors.append(
                ValidationIssue(
                    path="components",
                    message=f"Component count ({len(components)}) exceeds maximum limit ({MAX_COMPONENTS_LIMIT})",
                    code="EXCEED_COMPONENT_LIMIT",
                )
            )

        seen_ids = set()
        for idx, comp in enumerate(components):
            cid = comp.get("id")
            if cid in seen_ids:
                errors.append(
                    ValidationIssue(
                        path=f"components[{idx}].id",
                        message=f"Duplicate component instance ID '{cid}'",
                        code="DUPLICATE_COMPONENT_ID",
                    )
                )
            seen_ids.add(cid)

            try:
                self.component_registry.validate_instance(comp)
            except (
                ComponentNotFoundError,
                InvalidSlotPlacementError,
                InvalidComponentPropertyError,
                RetiredComponentError,
                MaliciousPayloadError,
            ) as e:
                path_str = f"components[{idx}]"
                if hasattr(e, "path") and e.path:
                    path_str = f"components[{idx}].props.{e.path}"
                errors.append(ValidationIssue(path=path_str, message=str(e), code="INVALID_COMPONENT"))

        if errors:
            return ValidationResult(is_valid=False, errors=errors)

        # Build normalized configuration
        normalized = json.loads(json.dumps(config))
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=warnings,
            normalized_configuration=normalized,
        )


_DEFAULT_VALIDATOR = CustomizationValidator()


def get_customization_validator() -> CustomizationValidator:
    return _DEFAULT_VALIDATOR
