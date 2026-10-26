from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

from fashx.core.errors import ValidationError

ALLOWED_CATEGORIES: set[str] = {
    "tops",
    "bottoms",
    "dresses",
    "outerwear",
}


@dataclass(frozen=True)
class NormalizedProduct:
    source_product_id: str
    title: str
    source_url: str
    category: str
    price_minor: int
    content_hash: str
    currency: str = "INR"
    in_stock: bool = True
    sizes_in_stock: tuple[str, ...] = ()
    subcategory: str | None = None
    description: str | None = None
    brand_id: UUID | None = None
    item_group_id: str | None = None


def normalize_product(row: dict[str, str]) -> NormalizedProduct:
    """Normalize and validate a raw product record against FashXStudio catalog invariants."""
    source_product_id = str(row.get("source_product_id", "")).strip()
    if not source_product_id:
        raise ValidationError("Missing required source_product_id", field="source_product_id")

    title = str(row.get("title", "")).strip()
    if not title:
        raise ValidationError("Missing required title", field="title")

    source_url = str(row.get("source_url", "")).strip()
    if not source_url:
        raise ValidationError("Missing required source_url", field="source_url")

    parsed_url = urlparse(source_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValidationError(
            f"Invalid source_url '{source_url}'; must be an absolute HTTP(S) URL with hostname",
            field="source_url",
        )

    category = str(row.get("category", "")).strip().lower()
    if category not in ALLOWED_CATEGORIES:
        raise ValidationError(
            f"Category '{category}' is not allowed; must be one of {sorted(ALLOWED_CATEGORIES)}",
            field="category",
        )

    price_raw = str(row.get("price_minor", "")).strip()
    try:
        price_minor = int(price_raw)
    except (ValueError, TypeError) as exc:
        raise ValidationError(
            f"Invalid price_minor '{price_raw}'; must be an integer",
            field="price_minor",
        ) from exc

    if price_minor < 0:
        raise ValidationError("price_minor cannot be negative", field="price_minor")

    currency = str(row.get("currency", "INR")).strip().upper() or "INR"

    in_stock_raw = str(row.get("in_stock", "true")).strip().lower()
    in_stock = in_stock_raw in {"true", "1", "yes", "t"}

    sizes_raw = str(row.get("sizes_in_stock", "")).strip()
    sizes: tuple[str, ...] = ()
    if sizes_raw:
        sep = "|" if "|" in sizes_raw else ","
        sizes = tuple(s.strip() for s in sizes_raw.split(sep) if s.strip())

    subcategory = str(row.get("subcategory", "")).strip() or None
    description = str(row.get("description", "")).strip() or None

    brand_id_raw = str(row.get("brand_id", "")).strip()
    brand_id: UUID | None = None
    if brand_id_raw:
        try:
            brand_id = UUID(brand_id_raw)
        except ValueError as exc:
            raise ValidationError(
                f"Invalid brand_id '{brand_id_raw}'; must be a valid UUID",
                field="brand_id",
            ) from exc

    item_group_id = str(row.get("item_group_id", "")).strip() or None

    # Deterministic fingerprint payload
    canonical_dict = {
        "source_product_id": source_product_id,
        "title": title,
        "source_url": source_url,
        "category": category,
        "price_minor": price_minor,
        "currency": currency,
        "in_stock": in_stock,
        "sizes_in_stock": list(sizes),
        "subcategory": subcategory,
        "description": description,
        "brand_id": str(brand_id) if brand_id else None,
        "item_group_id": item_group_id,
    }
    digest = hashlib.sha256(
        json.dumps(canonical_dict, sort_keys=True).encode("utf-8")
    ).hexdigest()

    return NormalizedProduct(
        source_product_id=source_product_id,
        title=title,
        source_url=source_url,
        category=category,
        price_minor=price_minor,
        currency=currency,
        in_stock=in_stock,
        sizes_in_stock=sizes,
        subcategory=subcategory,
        description=description,
        brand_id=brand_id,
        item_group_id=item_group_id,
        content_hash=digest,
    )


def read_csv_rows(path: Path) -> Iterator[tuple[int, dict[str, str]]]:
    """Read CSV rows safely; yields (line_number, row) for caller-level processing."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "source_product_id",
            "title",
            "source_url",
            "category",
            "price_minor",
        }
        headers = set(reader.fieldnames or [])
        missing = required - headers
        if missing:
            raise ValidationError(
                f"CSV is missing required columns: {', '.join(sorted(missing))}",
                field="csv_headers",
            )
        yield from enumerate(reader, start=2)
