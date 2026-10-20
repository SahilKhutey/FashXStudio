import csv
import hashlib
import pathlib
import sys
from collections import Counter
from decimal import Decimal, InvalidOperation
from typing import Any

REQUIRED = [
    "id",
    "title",
    "brand",
    "price",
    "gender",
    "category",
    "sub_category",
    "primary_color",
    "pattern",
    "formality",
    "ethnic_wear",
    "tryon_suitable",
    "sizes",
    "image",
]
CATEGORIES = {"top", "bottom", "one_piece", "outerwear"}
GENDERS = {"female", "male", "unisex"}
PATTERNS = {"solid", "striped", "checked", "floral", "printed", "embroidered", "other"}
SIZES = {"XS", "S", "M", "L", "XL", "XXL", "FREE"}
COLORS = {
    "black",
    "white",
    "grey",
    "beige",
    "brown",
    "red",
    "maroon",
    "orange",
    "yellow",
    "green",
    "teal",
    "blue",
    "navy",
    "purple",
    "pink",
    "multi",
}
SUB_SUGGESTED = {
    "tshirt",
    "shirt",
    "kurta",
    "kurti",
    "blouse",
    "hoodie",
    "jeans",
    "trousers",
    "skirt",
    "palazzo",
    "leggings",
    "dress",
    "kurta_set",
}


def main(path: str) -> int:
    p = pathlib.Path(path)
    if not p.exists():
        print(f"file not found: {path}")
        return 1
    rows = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
    errors: list[str] = []
    warns: list[str] = []
    if not rows:
        print("empty csv")
        return 1
    missing = [c for c in REQUIRED if c not in rows[0]]
    if missing:
        print(f"missing columns: {missing}")
        return 1
    seen_ids: set[str] = set()
    seen_hash: dict[str, str] = {}
    pil_image: Any = None
    try:
        from PIL import Image

        pil_image = Image
    except ImportError:
        warns.append("Pillow not installed: image sizes not checked")

    for n, r in enumerate(rows, start=2):  # row 1 is the header
        row_id = r.get("id", "?")

        def err(m: str, line: int = n, rid: str = row_id) -> None:
            errors.append(f"row {line} ({rid}): {m}")

        if not r["id"]:
            err("empty id")
        elif r["id"] in seen_ids:
            err("duplicate id")
        seen_ids.add(r["id"])
        if not r["title"].strip():
            err("empty title")
        try:
            if Decimal(r["price"]) <= 0:
                err("price must be positive")
        except InvalidOperation:
            err(f"price not a number: {r['price']!r}")
        if r["gender"] not in GENDERS:
            err(f"gender must be one of {sorted(GENDERS)}")
        if r["category"] not in CATEGORIES:
            err(f"category must be one of {sorted(CATEGORIES)}")
        if r["sub_category"] not in SUB_SUGGESTED:
            warns.append(f"row {n}: sub_category {r['sub_category']!r} not in the suggested list")
        if r["primary_color"] not in COLORS:
            err(f"primary_color must be one of {sorted(COLORS)}")
        if r["pattern"] not in PATTERNS:
            err(f"pattern must be one of {sorted(PATTERNS)}")
        if r["formality"] not in {"1", "2", "3", "4", "5"}:
            err("formality must be 1-5")
        for flag in ("ethnic_wear", "tryon_suitable"):
            if r[flag].lower() not in {"true", "false"}:
                err(f"{flag} must be true or false")
        sizes = [s for s in r["sizes"].split("|") if s]
        if not sizes or any(s not in SIZES for s in sizes):
            err(f"sizes must be a '|'-separated subset of {sorted(SIZES)}")
        img = p.parent / r["image"]
        if not img.exists():
            err(f"image not found: {r['image']}")
            continue
        if img.suffix.lower() not in {".jpg", ".jpeg"}:
            err("image must be a JPEG")
        h = hashlib.sha256(img.read_bytes()).hexdigest()
        if h in seen_hash:
            err(f"same image as {seen_hash[h]}")
        seen_hash[h] = r["id"]
        if pil_image:
            with pil_image.open(img) as im:
                if min(im.size) < 1000:
                    warns.append(
                        f"row {n}: {r['image']} is {im.size[0]}x{im.size[1]}; at least 1000 px on the short side is better"
                    )
    print(
        f"{len(rows)} rows | categories: {dict(Counter(r['category'] for r in rows))} | "
        f"try-on suitable: {sum(r['tryon_suitable'].lower() == 'true' for r in rows)}"
    )
    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/catalog/validate_csv.py catalog_seed/catalog.csv")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
