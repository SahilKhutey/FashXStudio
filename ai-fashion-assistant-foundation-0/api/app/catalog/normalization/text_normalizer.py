import re
from dataclasses import dataclass

PROMOTIONAL_PATTERNS = [
    r"\b\d+%\s*off\b",
    r"\bfree\s*shipping\b",
    r"\[.*?\]",
    r"\(trending\)",
    r"\(new\s*arrival\)",
    r"\bexclusive\b",
    r"\bbestseller\b",
    r"\blimited\s*edition\b",
    r"\bsale\b",
]

CATEGORY_RULES = [
    (
        "tops",
        "casual_shirts",
        [r"\bcasual\s*shirt\b", r"\boxford\s*shirt\b", r"\blinen\s*shirt\b", r"\bflannel\b"],
    ),
    ("tops", "formal_shirts", [r"\bformal\s*shirt\b", r"\bdress\s*shirt\b"]),
    ("tops", "polo_shirts", [r"\bpolo\b"]),
    ("tops", "t_shirts", [r"\bt-shirt\b", r"\btee\b", r"\btshirt\b"]),
    ("tops", "hoodies", [r"\bhoodie\b", r"\bsweatshirt\b"]),
    ("tops", "sweaters", [r"\bsweater\b", r"\bpullover\b", r"\bcardigan\b"]),
    ("bottoms", "jeans", [r"\bjeans\b", r"\bdenim\s*pants\b"]),
    ("bottoms", "chinos", [r"\bchinos\b", r"\bchino\b"]),
    ("bottoms", "trousers", [r"\btrousers\b", r"\bformal\s*pants\b", r"\bslacks\b"]),
    ("bottoms", "shorts", [r"\bshorts\b", r"\bbermuda\b"]),
    ("dresses", "casual_dresses", [r"\bcasual\s*dress\b", r"\bsundress\b", r"\bshirt\s*dress\b"]),
    ("dresses", "formal_dresses", [r"\bgown\b", r"\bevening\s*dress\b", r"\bcocktail\s*dress\b"]),
    ("outerwear", "blazers", [r"\bblazer\b", r"\bsuit\s*jacket\b"]),
    ("outerwear", "jackets", [r"\bjacket\b", r"\bbomber\b", r"\bwindbreaker\b"]),
    ("outerwear", "coats", [r"\bcoat\b", r"\btrench\b", r"\bparka\b"]),
]

FIT_PATTERNS = [
    ("slim", [r"\bslim\s*fit\b", r"\bslim\b"]),
    (
        "regular",
        [r"\bregular\s*fit\b", r"\bclassic\s*fit\b", r"\bregular\b", r"\bstandard\s*fit\b"],
    ),
    ("relaxed", [r"\brelaxed\s*fit\b", r"\bloose\s*fit\b", r"\boversized\b", r"\brelaxed\b"]),
    ("skinny", [r"\bskinny\s*fit\b", r"\bskinny\b"]),
]


@dataclass
class NormalizedTextAttributes:
    clean_title: str
    category: str
    subcategory: str | None
    inferred_fit: str | None


class TextNormalizer:
    """Cleans product titles and extracts standardized taxonomy classifications."""

    @classmethod
    def clean_title(cls, raw_title: str) -> str:
        """Strip promotional terms and extraneous whitespace from product titles."""
        text = raw_title
        for pat in PROMOTIONAL_PATTERNS:
            text = re.sub(pat, "", text, flags=re.IGNORECASE)
        # Clean dangling punctuation/symbols from stripped promo fragments
        text = re.sub(r"[\s\-_–!|:;,]+$", "", text)
        text = re.sub(r"^[\s\-_–!|:;,]+", "", text)
        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text).strip(" -_–!|:;,")
        return text

    @classmethod
    def infer_category_and_fit(
        cls, title: str, default_category: str = "tops"
    ) -> NormalizedTextAttributes:
        """Analyze title to extract clean title, category, subcategory, and fit."""
        clean = cls.clean_title(title)
        clean_lower = clean.lower()

        matched_category = default_category
        matched_subcategory: str | None = None

        for cat, subcat, patterns in CATEGORY_RULES:
            if any(re.search(pat, clean_lower) for pat in patterns):
                matched_category = cat
                matched_subcategory = subcat
                break

        matched_fit: str | None = None
        for fit_name, patterns in FIT_PATTERNS:
            if any(re.search(pat, clean_lower) for pat in patterns):
                matched_fit = fit_name
                break

        return NormalizedTextAttributes(
            clean_title=clean,
            category=matched_category,
            subcategory=matched_subcategory,
            inferred_fit=matched_fit,
        )
