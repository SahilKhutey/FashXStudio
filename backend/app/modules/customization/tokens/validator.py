import re
from typing import Any

ALLOWED_FONT_FAMILIES = {
    "system",
    "sans-serif",
    "serif",
    "monospace",
    "Inter",
    "Playfair Display",
    "Merriweather",
    "Cinzel",
    "Outfit",
    "Lora",
    "JetBrains Mono",
    "Courier New",
}

HEX_COLOR_REGEX = re.compile(r"^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
SPACING_UNIT_REGEX = re.compile(r"^(?:0(?:px|rem)?|[0-9]+(?:\.[0-9]+)?(?:rem|px))$")
CSS_INJECTION_REGEX = re.compile(
    r"url\(|expression\(|javascript:|binding:|behavior:|<script|@import",
    re.IGNORECASE,
)

ALLOWED_TOP_LEVEL_TOKEN_GROUPS = {
    "color",
    "typography",
    "spacing",
    "radius",
    "shadow",
    "border",
    "sizing",
    "motion",
    "breakpoints",
    "zIndex",
    "accessibility",
}


def validate_color(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if CSS_INJECTION_REGEX.search(value):
        return False
    return bool(HEX_COLOR_REGEX.match(value))


def validate_spacing(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if CSS_INJECTION_REGEX.search(value):
        return False
    return bool(SPACING_UNIT_REGEX.match(value))


def validate_font_family(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if CSS_INJECTION_REGEX.search(value):
        return False
    return value in ALLOWED_FONT_FAMILIES


def validate_token_overrides(overrides: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []

    def traverse(obj: Any, current_path: str) -> None:
        if not isinstance(obj, dict):
            errors.append(f"Invalid token override container at {current_path}")
            return

        for key, value in obj.items():
            next_path = f"{current_path}.{key}" if current_path else key

            if isinstance(value, str) and CSS_INJECTION_REGEX.search(value):
                errors.append(f"Arbitrary CSS expression rejected at {next_path}: {value}")
                continue

            if isinstance(value, dict):
                top_group = next_path.split(".")[0]
                if top_group not in ALLOWED_TOP_LEVEL_TOKEN_GROUPS:
                    errors.append(f"Unsupported token path: {next_path}")
                    continue
                traverse(value, next_path)
            else:
                top_group = next_path.split(".")[0]
                if top_group not in ALLOWED_TOP_LEVEL_TOKEN_GROUPS:
                    errors.append(f"Unsupported token path: {next_path}")
                    continue

                if next_path.startswith("color."):
                    if not validate_color(value):
                        errors.append(f"Invalid hex color at {next_path}: {value}")
                elif next_path.startswith("typography.fontFamily."):
                    if not validate_font_family(value):
                        errors.append(f"Unsupported font family at {next_path}: {value}")
                elif next_path.startswith("spacing."):
                    if not validate_spacing(value):
                        errors.append(f"Invalid spacing unit at {next_path}: {value}")

    traverse(overrides, "")
    return len(errors) == 0, errors
