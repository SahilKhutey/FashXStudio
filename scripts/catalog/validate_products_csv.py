"""Validate a product CSV before catalog ingestion.

This script validates file structure and basic product fields only.
It does not approve a source, establish rights, or import product data.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

REQUIRED_COLUMNS = {
    "source_product_id",
    "title",
    "source_url",
    "category",
    "price_minor",
    "currency",
    "in_stock",
}
MAX_ROWS = 10_000
MAX_FIELD_LENGTH = 4_000

APPROVED_CATEGORIES: set[str] = {
    "top",
    "tops",
    "shirt",
    "shirts",
    "tshirt",
    "tshirts",
    "bottom",
    "bottoms",
    "pants",
    "trousers",
    "jeans",
    "skirts",
    "one_piece",
    "one-piece",
    "one-pieces",
    "dress",
    "dresses",
    "jumpsuit",
    "outerwear",
    "jacket",
    "jackets",
    "coat",
    "coats",
    "sweater",
    "sweaters",
    "hoodie",
    "hoodies",
    "kurta",
    "kurtas",
    "ethnic",
    "accessories",
    "footwear",
}


def validate_row(row: dict[str, str], line: int) -> list[str]:
    """Validate a single product row against catalog constraints."""
    errors: list[str] = []

    for field in REQUIRED_COLUMNS:
        val = (row.get(field) or "").strip()
        if not val:
            errors.append(f"line {line}: {field} is required")
        elif len(val) > MAX_FIELD_LENGTH:
            errors.append(f"line {line}: {field} exceeds maximum length of {MAX_FIELD_LENGTH}")

    price_str = (row.get("price_minor") or "").strip()
    if price_str:
        try:
            price_val = int(price_str)
            if price_val < 0:
                errors.append(f"line {line}: price_minor cannot be negative (got {price_val})")
        except ValueError:
            errors.append(f"line {line}: price_minor must be an integer (got '{price_str}')")

    currency = (row.get("currency") or "").strip().upper()
    if currency and currency != "INR":
        errors.append(f"line {line}: currency must be 'INR' (got '{currency}')")

    source_url = (row.get("source_url") or "").strip()
    if source_url:
        parsed = urlparse(source_url)
        if parsed.scheme.lower() != "https" or not parsed.netloc:
            errors.append(f"line {line}: source_url must be a valid HTTPS URL (got '{source_url}')")

    category = (row.get("category") or "").strip().lower()
    if category and category not in APPROVED_CATEGORIES:
        errors.append(f"line {line}: category '{category}' not in approved taxonomy")

    in_stock_str = (row.get("in_stock") or "").strip().lower()
    if in_stock_str and in_stock_str not in {"true", "false", "1", "0", "yes", "no"}:
        errors.append(f"line {line}: in_stock must be a boolean ('true'/'false') (got '{in_stock_str}')")

    return errors


def validate_csv_file(csv_path: Path) -> tuple[bool, list[str], int]:
    """Validate full CSV structure, row constraints, and detect duplicate product IDs."""
    errors: list[str] = []

    if not csv_path.exists():
        return False, [f"File not found: {csv_path}"], 0

    if csv_path.stat().st_size == 0:
        return False, ["CSV file is empty"], 0

    seen_ids: dict[str, int] = {}
    total_rows = 0

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return False, ["CSV file has no header row"], 0

        header_fields = {col.strip() for col in reader.fieldnames if col}
        missing_cols = REQUIRED_COLUMNS - header_fields
        if missing_cols:
            errors.append(f"Missing required columns in CSV header: {sorted(missing_cols)}")
            return False, errors, 0

        for idx, row in enumerate(reader, start=2):
            total_rows += 1
            if total_rows > MAX_ROWS:
                errors.append(f"CSV exceeds maximum row limit of {MAX_ROWS}")
                break

            cleaned_row = {k.strip(): (v.strip() if v else "") for k, v in row.items() if k}
            row_errors = validate_row(cleaned_row, line=idx)
            errors.extend(row_errors)

            product_id = cleaned_row.get("source_product_id")
            if product_id:
                if product_id in seen_ids:
                    errors.append(
                        f"line {idx}: duplicate source_product_id '{product_id}' (first seen at line {seen_ids[product_id]})"
                    )
                else:
                    seen_ids[product_id] = idx

    is_valid = len(errors) == 0
    return is_valid, errors, total_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a product CSV before catalog ingestion.")
    parser.add_argument("csv_file", type=Path, help="Path to the product CSV file")
    parser.add_argument("--report", type=Path, default=None, help="Optional JSON report output path")

    args = parser.parse_args()

    is_valid, errors, total_rows = validate_csv_file(args.csv_file)

    report_data = {
        "valid": is_valid,
        "csv_file": str(args.csv_file),
        "total_rows": total_rows,
        "error_count": len(errors),
        "errors": errors,
    }

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        print(f"Validation report saved to {args.report}")

    if is_valid:
        print(f"CSV validation SUCCESS: {total_rows} row(s) checked, 0 errors.")
        sys.exit(0)
    else:
        print(f"CSV validation FAILED: {len(errors)} error(s) found in {total_rows} row(s):", file=sys.stderr)
        for err in errors[:20]:
            print(f"  - {err}", file=sys.stderr)
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
