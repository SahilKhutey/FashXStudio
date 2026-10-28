"""Normalization pipeline for external apparel products into FashXStudio catalog standard."""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from fashx.catalog.acquisition.contract import SourceProduct

# Canonical high-level categories
VALID_CANONICAL_CATEGORIES = {"tops", "bottoms", "dresses", "outerwear"}

# Mapping common retail categories and keywords to canonical (category, subcategory)
CATEGORY_MAPPINGS: list[tuple[re.Pattern, str, str]] = [
    # Tops
    (re.compile(r"\b(t[- ]?shirt|tee|polos?)\b", re.I), "tops", "tshirt"),
    (re.compile(r"\b(shirts?|button[- ]?down|chambray|flannel)\b", re.I), "tops", "shirt"),
    (re.compile(r"\b(sweaters?|pullovers?|knitwear|cardigans?)\b", re.I), "tops", "sweater"),
    (re.compile(r"\b(hoodies?|sweatshirts?)\b", re.I), "tops", "hoodie"),
    (re.compile(r"\b(blouses?|camisoles?|tank[- ]?tops?|tops?|tunics?)\b", re.I), "tops", "top"),
    # Dresses
    (re.compile(r"\b(midi[- ]?dress|maxi[- ]?dress|sundress|slip[- ]?dress|gowns?|dresses?)\b", re.I), "dresses", "dress"),
    # Bottoms
    (re.compile(r"\b(jeans?|denims?)\b", re.I), "bottoms", "jeans"),
    (re.compile(r"\b(trousers?|chinos?|slacks?|pants?)\b", re.I), "bottoms", "trousers"),
    (re.compile(r"\b(skirts?)\b", re.I), "bottoms", "skirt"),
    (re.compile(r"\b(shorts?)\b", re.I), "bottoms", "shorts"),
    # Outerwear
    (re.compile(r"\b(jackets?|bomber|trucker|chore|windbreaker)\b", re.I), "outerwear", "jacket"),
    (re.compile(r"\b(blazers?|suit[- ]?jackets?)\b", re.I), "outerwear", "blazer"),
    (re.compile(r"\b(coats?|overcoats?|parkas?|trench)\b", re.I), "outerwear", "coat"),
]

# Standard size label mappings
ALPHA_SIZES = {"XXS", "XS", "S", "M", "L", "XL", "XXL", "2XL", "3XL", "4XL"}
STRIP_TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "tag",
    "ref",
    "ref_",
    "pf_rd_r",
    "pf_rd_p",
}


class CatalogNormalizer:
    """Normalizes raw external source products into compliant canonical representations."""

    @classmethod
    def normalize_category(
        cls,
        raw_category: str,
        title: str = "",
        raw_subcategory: str | None = None,
    ) -> tuple[str, str | None]:
        """Map raw category/subcategory text to canonical (category, subcategory)."""
        combined = f"{raw_category} {raw_subcategory or ''} {title}".lower()

        for pattern, cat, subcat in CATEGORY_MAPPINGS:
            if pattern.search(combined):
                return cat, subcat

        # Fallback to direct match if raw category is already valid
        clean_raw = raw_category.strip().lower()
        if clean_raw in VALID_CANONICAL_CATEGORIES:
            return clean_raw, raw_subcategory.strip().lower() if raw_subcategory else None

        # Safe default
        return "tops", "shirt"

    @classmethod
    def normalize_brand(cls, raw_brand: str | None, title: str = "") -> str:
        """Extract or normalize brand name."""
        if raw_brand and raw_brand.strip():
            brand = raw_brand.strip()
            # Remove legal suffixes
            brand = re.sub(
                r"\s+(?:pvt\.?\s*ltd\.?|ltd\.?|llc|inc\.?|corp\.?|co\.?)$",
                "",
                brand,
                flags=re.I,
            )
            return brand.strip()

        # If missing, attempt extraction from leading title tokens (e.g., "Fabindia Men Cotton Shirt")
        if title:
            tokens = title.split()
            if tokens:
                return tokens[0].strip()

        return "Unknown"

    @classmethod
    def normalize_price_minor(cls, raw_price: int | float, currency: str = "INR") -> int:
        """Ensure price is positive integer in paise (minor units)."""
        if isinstance(raw_price, float):
            # If float looks like standard rupees (e.g. 1499.00), convert to paise
            return max(0, int(round(raw_price * 100)))
        if isinstance(raw_price, int):
            # If already minor units (>1000 for standard clothes), keep; otherwise check
            return max(0, raw_price)
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
            if clean in ALPHA_SIZES:
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
    def sanitize_url(cls, url: str) -> str:
        """Strip tracking parameters while preserving the core product path."""
        if not url:
            return ""
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return url

        query_params = parse_qsl(parsed.query, keep_blank_values=False)
        filtered_params = [
            (k, v) for k, v in query_params if k.lower() not in STRIP_TRACKING_PARAMS
        ]
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
        cat, subcat = cls.normalize_category(raw.category, raw.title, raw.subcategory)
        brand = cls.normalize_brand(raw.brand, raw.title)
        price_minor = cls.normalize_price_minor(raw.price_minor, raw.currency)
        sizes = cls.normalize_sizes(raw.sizes)
        sanitized_product_url = cls.sanitize_url(raw.product_url)
        sanitized_image_url = cls.sanitize_url(raw.image_url) if raw.image_url else None

        return SourceProduct(
            source_slug=raw.source_slug.strip().lower(),
            source_product_id=raw.source_product_id.strip(),
            title=raw.title.strip(),
            brand=brand,
            category=cat,
            subcategory=subcat,
            description=raw.description.strip() if raw.description else None,
            price_minor=price_minor,
            currency="INR",
            product_url=sanitized_product_url,
            image_url=sanitized_image_url,
            in_stock=bool(raw.in_stock) if raw.in_stock is not None else True,
            sizes=sizes,
            source_updated_at=raw.source_updated_at,
            image_rights=raw.image_rights,
            tryon_rights=raw.tryon_rights,
            raw_attributes=raw.raw_attributes,
        )
