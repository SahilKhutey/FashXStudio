"""Feed parsers for Google Merchant style CSV and XML streams."""

import csv
import io
from collections.abc import Iterator

from defusedxml import ElementTree as ET

from .model import CanonicalProduct, parse_price


def _bool_stock(v: str | None) -> bool:
    if not v:
        return True
    norm = v.strip().lower().replace("_", " ")
    return norm in {
        "in stock",
        "in_stock",
        "instock",
        "preorder",
        "backorder",
        "available",
        "true",
        "1",
        "yes",
    }


def map_row(r: dict[str, str]) -> CanonicalProduct:
    """Map raw feed row dictionary into a validated CanonicalProduct."""
    raw_price = r.get("price") or ""
    price, cur = parse_price(raw_price)
    if cur != "INR":
        raise ValueError(f"unsupported_currency: {cur}")

    raw_sale = r.get("sale_price")
    sale = None
    if raw_sale and raw_sale.strip():
        sale_val, sale_cur = parse_price(raw_sale)
        if sale_cur != "INR":
            raise ValueError(f"unsupported_currency in sale_price: {sale_cur}")
        sale = sale_val

    extra_images: list[str] = []
    add_images = r.get("additional_image_link") or r.get("extra_images") or ""
    if add_images:
        for u in add_images.split(","):
            u_str = u.strip()
            if u_str:
                extra_images.append(u_str)

    title = (r.get("title") or "").strip()
    desc = (r.get("description") or "").strip()
    link = (r.get("link") or "").strip()
    image_url = (r.get("image_link") or r.get("image_url") or "").strip()

    gender_val = (r.get("gender") or "").strip().lower() or None
    if gender_val not in {"female", "male", "unisex"}:
        gender_val = None

    source_category = (
        r.get("product_type")
        or r.get("google_product_category")
        or r.get("category")
        or None
    )

    return CanonicalProduct(
        source_product_id=str(r.get("id") or r.get("source_product_id") or "").strip(),
        item_group_id=(r.get("item_group_id") or "").strip() or None,
        title=title,
        description=desc,
        brand=(r.get("brand") or "").strip() or None,
        link=link,  # type: ignore[arg-type]
        image_url=image_url,  # type: ignore[arg-type]
        extra_image_urls=extra_images,  # type: ignore[arg-type]
        price=price,
        sale_price=sale,
        currency="INR",
        in_stock=_bool_stock(r.get("availability") or r.get("in_stock")),
        gender=gender_val,  # type: ignore[arg-type]
        age_group=(r.get("age_group") or "").strip().lower() or None,
        color=(r.get("color") or "").strip() or None,
        size=(r.get("size") or "").strip() or None,
        material=(r.get("material") or "").strip() or None,
        pattern=(r.get("pattern") or "").strip() or None,
        gtin=(r.get("gtin") or "").strip() or None,
        source_category=source_category.strip() if source_category else None,
    )


def rows_from_csv(data: bytes, delimiter: str = ",") -> Iterator[dict[str, str]]:
    """Yield feed rows from CSV bytes, handling UTF-8 BOM and multi-line fields."""
    text = io.TextIOWrapper(io.BytesIO(data), encoding="utf-8-sig", newline="")
    reader = csv.DictReader(text, delimiter=delimiter)
    for row in reader:
        # Strip string values and keys
        clean_row = {
            k.strip() if k else "": v.strip() if v else ""
            for k, v in row.items()
            if k is not None
        }
        if clean_row.get("id") or clean_row.get("title"):
            yield clean_row


def rows_from_xml(data: bytes) -> Iterator[dict[str, str]]:
    """Yield feed rows from XML bytes using defusedxml to prevent XML bomb & XXE attacks."""
    for _, el in ET.iterparse(io.BytesIO(data)):
        tag_name = el.tag.split("}")[-1]
        if tag_name in ("item", "entry"):
            row: dict[str, str] = {}
            for child in el:
                c_tag = child.tag.split("}")[-1]
                row[c_tag] = (child.text or "").strip()
            if row.get("id") or row.get("title"):
                yield row
            el.clear()
