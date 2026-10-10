"""Catalog field normalizers for categories, sizes, colors, and demographics."""

import re

INDIAN_COLOR_MAP: dict[str, str] = {
    "mehendi": "green",
    "mehndi": "green",
    "maroon": "red",
    "mustard": "yellow",
    "teal": "blue",
    "off-white": "white",
    "off white": "white",
    "rani pink": "pink",
    "pista": "green",
    "rust": "orange",
    "navy": "blue",
    "olive": "green",
    "khaki": "beige",
    "beige": "beige",
    "cream": "white",
    "black": "black",
    "white": "white",
    "red": "red",
    "blue": "blue",
    "green": "green",
    "yellow": "yellow",
    "pink": "pink",
    "grey": "grey",
    "gray": "grey",
    "brown": "brown",
    "orange": "orange",
    "purple": "purple",
    "gold": "yellow",
    "silver": "grey",
    "multicolor": "multicolor",
    "multi": "multicolor",
}

LETTER_SIZES = {"XXS", "XS", "S", "M", "L", "XL", "XXL", "2XL", "3XL", "4XL", "5XL"}


def normalize_color(raw_color: str | None) -> tuple[str | None, str | None]:
    """Normalize raw color text into (raw_color, base_color_family)."""
    if not raw_color or not raw_color.strip():
        return None, None
    raw = raw_color.strip()
    low = raw.lower()

    # Exact or substring match in Indian color map
    for k, v in INDIAN_COLOR_MAP.items():
        if k in low:
            return raw, v

    return raw, low.split()[0] if low else None


def normalize_size(raw_size: str | None) -> tuple[str | None, str | None]:
    """Normalize raw size text into (raw_size, canonical_size).

    Examples:
    'Medium' -> ('Medium', 'M')
    '38 (M)' -> ('38 (M)', 'M')
    'UK 10' -> ('UK 10', 'UK 10')
    'Free Size' -> ('Free Size', 'Free Size')
    'XL/2XL' -> ('XL/2XL', 'XL')
    """
    if not raw_size or not raw_size.strip():
        return None, None
    raw = raw_size.strip()
    clean = raw.upper().strip()

    if clean in {"FREE SIZE", "ONESIZE", "ONE SIZE", "FREE"}:
        return raw, "Free Size"

    # Match expressions like "38 (M)" or "(L)"
    m_paren = re.search(r"\(([A-Z0-9]+)\)", clean)
    if m_paren and m_paren.group(1) in LETTER_SIZES:
        return raw, m_paren.group(1)

    # Match letter sizes
    if clean in {"SMALL", "S"}:
        return raw, "S"
    if clean in {"MEDIUM", "M"}:
        return raw, "M"
    if clean in {"LARGE", "L"}:
        return raw, "L"
    if clean in {"X-LARGE", "XL"}:
        return raw, "XL"
    if clean in {"XX-LARGE", "XXL", "2XL"}:
        return raw, "2XL"
    if clean in {"3XL", "XXXL"}:
        return raw, "3XL"
    if clean in {"XS", "EXTRA SMALL"}:
        return raw, "XS"

    # Match split like "XL/2XL"
    if "/" in clean:
        parts = clean.split("/")
        first = parts[0].strip()
        if first in LETTER_SIZES:
            return raw, first

    # Match UK/EU/US shoe/dress sizes
    m_region = re.match(r"^(UK|EU|US)\s*(\d+(?:\.\d+)?)$", clean)
    if m_region:
        return raw, f"{m_region.group(1)} {m_region.group(2)}"

    # Match numeric waist sizes like 28, 30, 32, 34
    m_num = re.match(r"^(\d{2})$", clean)
    if m_num:
        return raw, m_num.group(1)

    return raw, raw


def validate_age_group(raw_age_group: str | None) -> None:
    """Validate age group. Raises Reject('out_of_scope') for kids/infants."""
    from .safe_http import Reject

    if not raw_age_group:
        return
    low = raw_age_group.strip().lower()
    if any(k in low for k in ("kid", "child", "infant", "toddler", "baby", "boy", "girl")):
        raise Reject("out_of_scope")
