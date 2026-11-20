"""Normalization pipeline for external apparel products into FashXStudio catalog standard."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from fashx.catalog.acquisition.contract import SourceProduct

# Canonical high-level categories
VALID_CANONICAL_CATEGORIES = {"tops", "bottoms", "dresses", "outerwear"}

# Mapping common retail categories and keywords to canonical (category, subcategory)
CATEGORY_MAPPINGS: list[tuple[re.Pattern, str, str]] = [
    # Tops
    (re.compile(r"\b(t[- ]?shirt|tee|polos?)\b", re.I), "tops", "tshirt"),
    (
        re.compile(r"\b(shirts?|button[- ]?down|chambray|flannel|kurta|kurti)\b", re.I),
        "tops",
        "shirt",
    ),
    (re.compile(r"\b(sweaters?|pullovers?|knitwear|cardigans?)\b", re.I), "tops", "sweater"),
    (re.compile(r"\b(hoodies?|sweatshirts?)\b", re.I), "tops", "hoodie"),
    (re.compile(r"\b(blouses?|camisoles?|tank[- ]?tops?|tops?|tunics?)\b", re.I), "tops", "top"),
    # Dresses
    (
        re.compile(
            r"\b(midi[- ]?dress|maxi[- ]?dress|sundress|slip[- ]?dress|gowns?|dresses?|saree|sari|anarkali|lehenga)\b",
            re.I,
        ),
        "dresses",
        "dress",
    ),
    # Bottoms
    (re.compile(r"\b(jeans?|denims?)\b", re.I), "bottoms", "jeans"),
    (
        re.compile(r"\b(trousers?|chinos?|slacks?|pants?|palazzos?|leggings?)\b", re.I),
        "bottoms",
        "trousers",
    ),
    (re.compile(r"\b(skirts?)\b", re.I), "bottoms", "skirt"),
    (re.compile(r"\b(shorts?)\b", re.I), "bottoms", "shorts"),
    # Outerwear
    (
        re.compile(r"\b(jackets?|bomber|trucker|chore|windbreaker|shrugs?)\b", re.I),
        "outerwear",
        "jacket",
    ),
    (re.compile(r"\b(blazers?|suit[- ]?jackets?)\b", re.I), "outerwear", "blazer"),
    (re.compile(r"\b(coats?|overcoats?|parkas?|trench)\b", re.I), "outerwear", "coat"),
]

# Standard size label mappings
ALPHA_SIZES = {"XXS", "XS", "S", "M", "L", "XL", "XXL", "2XL", "3XL", "4XL", "ONE_SIZE"}
ONE_SIZE_ALIASES = {"FREE SIZE", "ONE SIZE", "FREESIZE", "ONESIZE", "FS", "OS", "UNIVERSAL"}

# Non-essential tracking parameters to strip
STRIP_TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "pf_rd_r",
    "pf_rd_p",
}

# Parameters that must be preserved for affiliate attribution
PRESERVED_AFFILIATE_PARAMS = {
    "tag",
    "ref",
    "ref_",
    "affid",
    "aff_id",
    "clickid",
    "click_id",
    "subid",
    "sub_id",
}

CURRENCY_EXPONENT: dict[str, int] = {
    "INR": 2,
    "USD": 2,
    "EUR": 2,
    "GBP": 2,
    "JPY": 0,
    "AUD": 2,
    "CAD": 2,
    "SGD": 2,
    "AED": 2,
}

COLOR_FAMILY_MAP: dict[str, str] = {
    "mehendi": "Green",
    "mehndi": "Green",
    "pista": "Green",
    "olive": "Green",
    "green": "Green",
    "dark green": "Green",
    "mint": "Green",
    "rani pink": "Pink",
    "pink": "Pink",
    "baby pink": "Pink",
    "rose": "Pink",
    "magenta": "Pink",
    "wine": "Red",
    "maroon": "Red",
    "red": "Red",
    "crimson": "Red",
    "burgundy": "Red",
    "mustard": "Yellow",
    "yellow": "Yellow",
    "ochre": "Yellow",
    "rust": "Orange",
    "orange": "Orange",
    "peach": "Orange",
    "coral": "Orange",
    "navy": "Blue",
    "blue": "Blue",
    "indigo": "Blue",
    "sky blue": "Blue",
    "royal blue": "Blue",
    "teal": "Blue",
    "off white": "White",
    "white": "White",
    "cream": "White",
    "ivory": "White",
    "beige": "White",
    "charcoal": "Grey",
    "grey": "Grey",
    "gray": "Grey",
    "slate": "Grey",
    "black": "Black",
    "brown": "Brown",
    "tan": "Brown",
    "khaki": "Brown",
    "purple": "Purple",
    "lavender": "Purple",
    "violet": "Purple",
    "multicolor": "Multicolor",
    "multi": "Multicolor",
}


@dataclass(frozen=True)
class CategoryResult:
    """Canonical category resolution outcome."""

    category: str | None
    subcategory: str | None
    mapped: bool
    mapping_version: str = "v1"


def to_minor_units(raw_price: str | int | float | Decimal, currency: str = "INR") -> int:
    """Convert price into minor units using ISO 4217 exponents and exact Decimal math."""
    curr = currency.upper().strip()
    if curr not in CURRENCY_EXPONENT:
        raise ValueError("unsupported_currency")

    try:
        amount = Decimal(str(raw_price))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("invalid_price") from exc

    if not amount.is_finite() or amount <= 0:
        raise ValueError("price_must_be_positive_and_finite")

    exponent = CURRENCY_EXPONENT[curr]
    scale = Decimal(10) ** exponent
    return int((amount * scale).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


class CatalogNormalizer:
    """Normalizes raw external source products into compliant canonical representations."""

    @classmethod
    def normalize_category_result(
        cls,
        raw_category: str | None,
        title: str = "",
        raw_subcategory: str | None = None,
    ) -> CategoryResult:
        """Map raw category/subcategory text to canonical CategoryResult."""
        if not raw_category or not str(raw_category).strip():
            return CategoryResult(None, None, False, "v1")

        combined = f"{raw_category} {raw_subcategory or ''} {title}".lower()

        for pattern, cat, subcat in CATEGORY_MAPPINGS:
            if pattern.search(combined):
                return CategoryResult(
                    category=cat, subcategory=subcat, mapped=True, mapping_version="v1"
                )

        # Check if raw category is already a valid canonical category
        clean_raw = raw_category.strip().lower()
        if clean_raw in VALID_CANONICAL_CATEGORIES:
            return CategoryResult(
                category=clean_raw,
                subcategory=raw_subcategory.strip().lower() if raw_subcategory else None,
                mapped=True,
                mapping_version="v1",
            )

        # Unmapped: do NOT silently fallback to "tops/shirt"!
        return CategoryResult(None, None, False, "v1")

    @classmethod
    def normalize_category(
        cls,
        raw_category: str | None,
        title: str = "",
        raw_subcategory: str | None = None,
    ) -> tuple[str, str | None]:
        """Legacy helper returning tuple[str, str | None]."""
        res = cls.normalize_category_result(raw_category, title, raw_subcategory)
        if res.mapped and res.category:
            return res.category, res.subcategory
        return "unmapped", None

    @classmethod
    def normalize_brand(cls, raw_brand: str | None, title: str = "") -> str:
        """Normalize brand name, inferring from title when absent or defaulting to Unknown."""
        if not raw_brand or not str(raw_brand).strip():
            if title and str(title).strip():
                tokens = str(title).strip().split()
                if tokens:
                    return tokens[0]
            return "Unknown"

        value = unicodedata.normalize("NFKC", str(raw_brand))
        value = re.sub(r"\s+", " ", value).strip()
        if len(value) > 120:
            raise ValueError("brand_too_long")

        if value.casefold() in {"unknown", "n/a", "na", "none", "generic"}:
            return "Unknown"

        # Remove legal suffixes
        value = re.sub(
            r"\s+(?:pvt\.?\s*ltd\.?|ltd\.?|llc|inc\.?|corp\.?|co\.?)$",
            "",
            value,
            flags=re.I,
        ).strip()
        return value or "Unknown"

    @classmethod
    def normalize_price_minor(
        cls, raw_price: int | float | str | Decimal, currency: str = "INR"
    ) -> int:
        """Convert raw price into integer minor units."""
        if isinstance(raw_price, int) and raw_price > 0:
            # If already minor integer units, preserve
            return raw_price
        try:
            return to_minor_units(raw_price, currency)
        except Exception:
            return 0

    @classmethod
    def normalize_sizes(cls, raw_sizes: tuple[str, ...] | list[str] | str) -> tuple[str, ...]:
        """Normalize size strings into clean canonical tuples."""
        if isinstance(raw_sizes, str):
            raw_list = [s.strip() for s in re.split(r"[,|/]", raw_sizes) if s.strip()]
        else:
            raw_list = [str(s).strip() for s in raw_sizes if str(s).strip()]

        normalized: list[str] = []
        for s in raw_list:
            clean = s.upper().replace(" ", "")
            clean_with_spaces = s.upper().strip()
            if clean_with_spaces in ONE_SIZE_ALIASES or clean in ONE_SIZE_ALIASES:
                if "ONE_SIZE" not in normalized:
                    normalized.append("ONE_SIZE")
            elif clean in ALPHA_SIZES:
                if clean not in normalized:
                    normalized.append(clean)
            elif clean.isdigit():
                # Waist/numerical size (e.g. 28, 30, 32, 34, 36)
                if clean not in normalized:
                    normalized.append(clean)
            else:
                # Retain clean non-empty size token
                if clean and clean not in normalized:
                    normalized.append(clean)

        return tuple(normalized)

    @classmethod
    def normalize_color(cls, raw_color: str | None) -> tuple[str | None, str | None]:
        """Normalize color to (raw_color_cleaned, canonical_family)."""
        if not raw_color or not str(raw_color).strip():
            return None, None

        cleaned = str(raw_color).strip()
        norm_key = cleaned.lower()

        # Check exact match
        if norm_key in COLOR_FAMILY_MAP:
            return cleaned, COLOR_FAMILY_MAP[norm_key]

        # Check partial/contains match
        for key, family in COLOR_FAMILY_MAP.items():
            if key in norm_key:
                return cleaned, family

        return cleaned, cleaned.capitalize()

    @classmethod
    def sanitize_url(cls, url: str, preserve_affiliate: bool = False) -> str:
        """Strip tracking parameters while preserving the core product path and affiliate attribution."""
        if not url:
            return ""
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return url

        query_params = parse_qsl(parsed.query, keep_blank_values=False)
        filtered_params: list[tuple[str, str]] = []

        for k, v in query_params:
            k_lower = k.lower()
            if k_lower in STRIP_TRACKING_PARAMS:
                continue
            if not preserve_affiliate and k_lower in PRESERVED_AFFILIATE_PARAMS:
                continue
            filtered_params.append((k, v))

        new_query = urlencode(filtered_params)
        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment,
            )
        )

    @classmethod
    def normalize_product(cls, raw: SourceProduct) -> SourceProduct:
        """Apply full normalization pipeline to a SourceProduct."""
        cat_res = cls.normalize_category_result(raw.category, raw.title, raw.subcategory)
        cat = cat_res.category if cat_res.mapped and cat_res.category else "unmapped"
        subcat = cat_res.subcategory if cat_res.mapped else None
        brand = cls.normalize_brand(raw.brand, raw.title)
        currency = raw.currency.upper().strip() if raw.currency else "INR"
        price_minor = cls.normalize_price_minor(raw.price_minor, currency)
        sizes = cls.normalize_sizes(raw.sizes)
        sanitized_product_url = cls.sanitize_url(raw.product_url, preserve_affiliate=True)
        sanitized_image_url = (
            cls.sanitize_url(raw.image_url, preserve_affiliate=False) if raw.image_url else None
        )

        return SourceProduct(
            source_slug=raw.source_slug.strip().lower(),
            source_product_id=raw.source_product_id.strip(),
            title=raw.title.strip(),
            brand=brand,
            category=cat,
            subcategory=subcat,
            description=raw.description.strip() if raw.description else None,
            price_minor=price_minor,
            currency=currency,
            product_url=sanitized_product_url,
            image_url=sanitized_image_url,
            in_stock=raw.in_stock,
            sizes=sizes,
            source_updated_at=raw.source_updated_at,
            image_rights=raw.image_rights,
            tryon_rights=raw.tryon_rights,
            prepared_image_key=raw.prepared_image_key,
            prepared_image_hash=raw.prepared_image_hash,
            raw_attributes=raw.raw_attributes,
        )
