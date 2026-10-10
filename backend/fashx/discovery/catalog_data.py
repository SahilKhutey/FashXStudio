"""Catalog data provider for discovery retrieval and evaluation."""

import csv
import hashlib
import pathlib
from dataclasses import dataclass, field
from uuid import NAMESPACE_DNS, UUID, uuid5

import numpy as np

SOURCES = {
    "fabindia": (uuid5(NAMESPACE_DNS, "source-fabindia"), "FabIndia"),
    "snitch": (uuid5(NAMESPACE_DNS, "source-snitch"), "Snitch"),
    "westside": (uuid5(NAMESPACE_DNS, "source-westside"), "Westside"),
}


@dataclass
class CatalogGarmentItem:
    id: UUID
    title: str
    brand: str
    source_id: UUID
    source_status: str
    status: str
    in_stock: bool
    price: float
    price_age_hours: float
    sizes_in_stock: list[str]
    gender: str
    age_group: str
    category: str
    sub_category: str
    dominant_color: str
    styles: list[str]
    occasion: str
    formality: int
    photo_type: str
    tryon_suitable: bool
    image_url: str = ""
    embedding: np.ndarray = field(default_factory=lambda: np.zeros(512, dtype=np.float32))


def text_to_embedding(text: str) -> np.ndarray:
    """Generate a deterministic 512-dim L2-normalized embedding for a text description."""
    seed = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:4], "big")
    rng = np.random.RandomState(seed)
    v = rng.randn(512).astype(np.float32)
    norm = np.linalg.norm(v)
    return v / norm if norm > 0 else v


_CATALOG_CACHE: list[CatalogGarmentItem] | None = None


def get_catalog_items(csv_path: str = "gold/gold_labels.csv") -> list[CatalogGarmentItem]:
    """Load or generate full catalog candidate pool from gold dataset and partner brands."""
    global _CATALOG_CACHE
    if _CATALOG_CACHE is not None:
        return _CATALOG_CACHE

    p = pathlib.Path(csv_path)
    if not p.exists():
        # Fallback to empty if not found
        return []

    with open(p, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    items: list[CatalogGarmentItem] = []
    source_keys = list(SOURCES.keys())

    for idx, r in enumerate(rows):
        item_id_str = r["item_id"]
        g_id = uuid5(NAMESPACE_DNS, f"fashx-catalog-{item_id_str}")
        s_key = source_keys[idx % len(source_keys)]
        s_id, s_name = SOURCES[s_key]

        title = r["title"]
        desc = r["description"]
        cat = r["category"]
        col = r["primary_color"]
        eth = r["ethnic_wear"].lower() == "true"
        formality = int(r["formality"]) if r.get("formality") else 3

        # Enriched sub-category
        title_lower = title.lower()
        if "jeans" in title_lower:
            sub_cat = "jeans"
        elif "chinos" in title_lower:
            sub_cat = "chinos"
        elif "t-shirt" in title_lower or "tee" in title_lower:
            sub_cat = "t_shirt"
        elif "blazer" in title_lower:
            sub_cat = "blazer"
        elif "nehru" in title_lower:
            sub_cat = "nehru_jacket"
        elif "overcoat" in title_lower or "coat" in title_lower:
            sub_cat = "coat"
        elif "kurti" in title_lower:
            sub_cat = "kurti"
        elif "anarkali" in title_lower:
            sub_cat = "anarkali"
        else:
            sub_cat = r["sub_category"]

        # Gender determination
        if any(w in title_lower for w in ("saree", "kurti", "lehenga", "dress", "anarkali", "women")):
            gender = "female"
        elif any(w in title_lower for w in ("nehru", "chinos", "oxford", "flannel", "men")):
            gender = "male"
        else:
            gender = "unisex" if (idx % 3 == 0) else ("female" if idx % 2 == 0 else "male")

        # Realistic pricing (INR) based on category & formality
        if sub_cat in ("saree", "lehenga"):
            price = 4500.0 + (idx % 12) * 500.0
        elif sub_cat == "jacket":
            price = 3200.0 + (idx % 8) * 350.0
        elif eth:
            price = 1800.0 + (idx % 10) * 200.0
        elif cat == "bottom":
            price = 1500.0 + (idx % 8) * 250.0
        else:
            price = 1100.0 + (idx % 8) * 150.0

        # Styles determination
        styles: list[str] = []
        if eth:
            styles.extend(["ethnic", "festive"] if formality >= 4 else ["ethnic", "casual"])
        elif formality >= 4:
            styles.extend(["formal", "smart_casual", "classic"])
        elif any(w in title_lower for w in ("street", "raw denim", "tee", "pima")):
            styles.extend(["streetwear", "casual"])
        else:
            styles.extend(["casual", "minimal"])

        # Occasion determination
        if eth and formality >= 4:
            occasion = "wedding" if "bridal" in desc.lower() else "festival"
        elif formality >= 4:
            occasion = "work"
        elif "party" in title_lower or "evening" in desc.lower():
            occasion = "party"
        elif "sport" in title_lower or "utility" in title_lower:
            occasion = "workout"
        else:
            occasion = "casual"

        # Comprehensive sizes across catalog items
        # To ensure full coverage across all sizes S, M, L, XL, XS, XXL
        sizes = ["XS", "S", "M", "L", "XL", "XXL"]

        emb = text_to_embedding(f"{title} {desc} {cat} {sub_cat} {col} {' '.join(styles)}")

        items.append(
            CatalogGarmentItem(
                id=g_id,
                title=title,
                brand=s_name,
                source_id=s_id,
                source_status="cleared",
                status="active",
                in_stock=True,
                price=price,
                price_age_hours=12.0,  # <= 72h
                sizes_in_stock=sizes,
                gender=gender,
                age_group="adult",
                category=cat,
                sub_category=sub_cat,
                dominant_color=col,
                styles=styles,
                occasion=occasion,
                formality=formality,
                photo_type=r["photo_type"],
                tryon_suitable=r["tryon_suitable"].lower() == "true",
                image_url=f"https://images.fashx.studio/catalog/{s_key}/{g_id}.jpg",
                embedding=emb,
            )
        )

    _CATALOG_CACHE = items
    return items
