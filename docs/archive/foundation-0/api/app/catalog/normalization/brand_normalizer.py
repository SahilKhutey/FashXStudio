import re

BRAND_ALIAS_MAP: dict[str, str] = {
    "hm": "H&M",
    "hennesmauritz": "H&M",
    "zara": "Zara",
    "zaraman": "Zara",
    "zarawoman": "Zara",
    "zarabasic": "Zara",
    "uniqlo": "Uniqlo",
    "uniqlou": "Uniqlo",
    "levis": "Levi's",
    "levistrauss": "Levi's",
    "mango": "Mango",
    "mangoman": "Mango",
    "nike": "Nike",
    "adidas": "Adidas",
    "marksspencer": "Marks & Spencer",
    "ms": "Marks & Spencer",
    "snitch": "Snitch",
    "fabindia": "Fabindia",
}


class BrandNormalizer:
    """Normalizes retailer brand names and maps variations to canonical brand names."""

    @staticmethod
    def normalize_key(name: str) -> str:
        """Strip punctuation, 'and', whitespace, and lowercase for robust matching."""
        lower = name.lower()
        lower = re.sub(r"\band\b", "", lower)
        return re.sub(r"[^a-zA-Z0-9]", "", lower)

    @classmethod
    def resolve_brand(cls, raw_name: str) -> tuple[str, str]:
        """Resolve a raw brand name into (canonical_name, normalized_key).

        Example:
            "H & M" -> ("H&M", "hm")
            "h and m" -> ("H&M", "hm")
            "Levi's" -> ("Levi's", "levis")
        """
        raw_clean = raw_name.strip()
        key = cls.normalize_key(raw_clean)

        # Check direct lookup by normalized key
        if key in BRAND_ALIAS_MAP:
            return BRAND_ALIAS_MAP[key], key

        # Fallback to Title Cased cleaned name
        canonical = raw_clean.title()
        return canonical, key
