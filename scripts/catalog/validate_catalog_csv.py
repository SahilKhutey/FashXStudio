#!/usr/bin/env python3
"""Validate a FashXStudio apparel catalog CSV before ingestion."""

from __future__ import annotations

import argparse
import csv
import ipaddress
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

REQUIRED_COLUMNS = {
    "source_slug",
    "source_product_id",
    "title",
    "brand",
    "category",
    "subcategory",
    "price_minor",
    "currency",
    "in_stock",
    "size_values",
    "product_url",
    "image_url",
    "image_rights",
    "tryon_rights",
}

VALID_CATEGORIES = {"tops", "bottoms", "dresses", "outerwear"}
VALID_CURRENCIES = {"INR"}
VALID_RIGHTS = {"owned", "licensed", "partner_authorized"}
TRUE_VALUES = {"true", "1", "yes"}
FALSE_VALUES = {"false", "0", "no"}
SLUG_PATTERN = re.compile(r"^[a-z0-9_-]+$")


def is_safe_https_url(url_str: str) -> tuple[bool, str]:
    """Verify that URL is a valid, well-formed HTTPS URL not targeting private/local networks."""
    if not url_str or not isinstance(url_str, str):
        return False, "URL is empty"
    try:
        parsed = urlparse(url_str.strip())
    except Exception as e:
        return False, f"Malformed URL: {e}"

    if parsed.scheme.lower() != "https":
        return False, f"Scheme must be 'https', got '{parsed.scheme}'"

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return False, "URL host is missing"

    # Block localhost and private IP addresses
    if hostname in {"localhost", "127.0.0.1", "0.0.0.0", "::1"} or hostname.endswith(".local"):
        return False, f"Forbidden local/internal host: '{hostname}'"

    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False, f"Forbidden private/reserved IP host: '{hostname}'"
    except ValueError:
        # Not an IP literal; valid domain name
        pass

    return True, ""


def validate_catalog_csv(path: Path | str) -> list[str]:
    """Validate a catalog CSV file and return a list of error strings."""
    csv_path = Path(path)
    if not csv_path.exists():
        return [f"File not found: '{csv_path}'"]

    errors: list[str] = []
    try:
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return ["CSV file is empty or missing header."]

            fieldnames_set = set(reader.fieldnames)
            missing_cols = sorted(REQUIRED_COLUMNS - fieldnames_set)
            if missing_cols:
                return [f"Missing required header columns: {', '.join(missing_cols)}"]

            seen_product_ids: set[str] = set()
            row_count = 0

            for line_no, row in enumerate(reader, start=2):
                row_count += 1
                row_id = (row.get("source_product_id") or "").strip()

                # 1. source_slug
                slug = (row.get("source_slug") or "").strip()
                if not slug:
                    errors.append(f"Row {line_no}: 'source_slug' cannot be empty")
                elif not SLUG_PATTERN.match(slug):
                    errors.append(f"Row {line_no}: 'source_slug' '{slug}' must match pattern '^[a-z0-9_-]+$'")

                # 2. source_product_id
                if not row_id:
                    errors.append(f"Row {line_no}: 'source_product_id' cannot be empty")
                elif row_id in seen_product_ids:
                    errors.append(f"Row {line_no}: Duplicate 'source_product_id' '{row_id}'")
                seen_product_ids.add(row_id)

                # 3. title
                title = (row.get("title") or "").strip()
                if not title:
                    errors.append(f"Row {line_no} ({row_id}): 'title' cannot be empty")

                # 4. brand
                brand = (row.get("brand") or "").strip()
                if not brand:
                    errors.append(f"Row {line_no} ({row_id}): 'brand' cannot be empty")

                # 5. category
                cat = (row.get("category") or "").strip().lower()
                if cat not in VALID_CATEGORIES:
                    errors.append(
                        f"Row {line_no} ({row_id}): Invalid 'category' '{cat}'. "
                        f"Must be one of {sorted(VALID_CATEGORIES)}"
                    )

                # 6. price_minor
                price_str = (row.get("price_minor") or "").strip()
                try:
                    price_val = int(price_str)
                    if price_val <= 0:
                        errors.append(f"Row {line_no} ({row_id}): 'price_minor' must be > 0, got {price_val}")
                except ValueError:
                    errors.append(f"Row {line_no} ({row_id}): 'price_minor' must be an integer, got '{price_str}'")

                # 7. currency
                curr = (row.get("currency") or "").strip().upper()
                if curr not in VALID_CURRENCIES:
                    errors.append(
                        f"Row {line_no} ({row_id}): Invalid 'currency' '{curr}'. Must be {sorted(VALID_CURRENCIES)}"
                    )

                # 8. in_stock
                stock_str = (row.get("in_stock") or "").strip().lower()
                if stock_str not in (TRUE_VALUES | FALSE_VALUES):
                    errors.append(f"Row {line_no} ({row_id}): 'in_stock' must be boolean (true/false), got '{stock_str}'")

                # 9. size_values
                sizes_str = (row.get("size_values") or "").strip()
                sizes = [s.strip() for s in sizes_str.split("|") if s.strip()]
                if not sizes:
                    errors.append(f"Row {line_no} ({row_id}): 'size_values' must contain at least one size separated by '|'")

                # 10. product_url
                prod_url = (row.get("product_url") or "").strip()
                valid_prod_url, prod_url_err = is_safe_https_url(prod_url)
                if not valid_prod_url:
                    errors.append(f"Row {line_no} ({row_id}): Invalid 'product_url': {prod_url_err}")

                # 11. image_url
                img_url = (row.get("image_url") or "").strip()
                valid_img_url, img_url_err = is_safe_https_url(img_url)
                if not valid_img_url:
                    errors.append(f"Row {line_no} ({row_id}): Invalid 'image_url': {img_url_err}")

                # 12. image_rights
                rights = (row.get("image_rights") or "").strip().lower()
                if rights not in VALID_RIGHTS:
                    errors.append(
                        f"Row {line_no} ({row_id}): Invalid 'image_rights' '{rights}'. "
                        f"Must be one of {sorted(VALID_RIGHTS)}"
                    )

                # 13. tryon_rights
                tryon_str = (row.get("tryon_rights") or "").strip().lower()
                if tryon_str not in (TRUE_VALUES | FALSE_VALUES):
                    errors.append(f"Row {line_no} ({row_id}): 'tryon_rights' must be boolean (true/false), got '{tryon_str}'")

            if row_count == 0:
                errors.append("CSV contains header but no product rows.")

    except Exception as e:
        return [f"Failed to read CSV: {e}"]

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate FashXStudio catalog CSV")
    parser.add_argument("csv_path", type=Path, help="Path to apparel catalog CSV")
    args = parser.parse_args()

    errors = validate_catalog_csv(args.csv_path)
    if errors:
        print(f"FAILED: {len(errors)} validation error(s) found in {args.csv_path}:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"VALIDATION PASSED: {args.csv_path} is structurally valid and safe for ingestion.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
