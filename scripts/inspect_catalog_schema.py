"""Helper script to inspect catalog database models, constraints, and indexes."""

from __future__ import annotations

import sys
from typing import Any

import database.models.catalog  # noqa: F401
import database.models.catalog_freshness  # noqa: F401
import database.models.catalog_image  # noqa: F401
from database.models import Base


def inspect_catalog_schema() -> dict[str, Any]:
    metadata = Base.metadata
    target_tables = [
        "merchants",
        "catalog_sources",
        "canonical_garments",
        "merchant_products",
        "merchant_offers",
        "size_definitions",
        "product_variants",
        "merchant_offer_sizes",
        "merchant_offer_price_history",
        "catalog_provenance_records",
        "catalog_image_assets",
        "ingest_runs",
    ]

    schema_report: dict[str, Any] = {}

    print("=" * 70)
    print("FASHXSTUDIO CATALOG DATABASE SCHEMA INSPECTION (PHASE 05.5)")
    print("=" * 70)

    for table_name in target_tables:
        table = metadata.tables.get(table_name)
        if table is None:
            print(f"[-] TABLE MISSING: {table_name}")
            schema_report[table_name] = {"found": False}
            continue

        columns = [
            {
                "name": col.name,
                "type": str(col.type),
                "nullable": col.nullable,
                "primary_key": col.primary_key,
                "foreign_keys": [str(fk.target_fullname) for fk in col.foreign_keys],
            }
            for col in table.columns
        ]

        indexes = [
            {
                "name": idx.name,
                "columns": [col.name for col in idx.columns],
                "unique": idx.unique,
            }
            for idx in table.indexes
        ]

        uniques = [
            {
                "name": uq.name,
                "columns": [col.name for col in uq.columns],
            }
            for uq in table.constraints
            if getattr(uq, "name", None) and uq.__class__.__name__ == "UniqueConstraint"
        ]

        schema_report[table_name] = {
            "found": True,
            "columns_count": len(columns),
            "columns": columns,
            "indexes_count": len(indexes),
            "indexes": indexes,
            "uniques": uniques,
        }

        print(f"\n[+] Table: {table_name} ({len(columns)} columns, {len(indexes)} indexes)")
        for col in columns:
            fk_str = f" -> FK({', '.join(col['foreign_keys'])})" if col["foreign_keys"] else ""
            pk_str = " [PK]" if col["primary_key"] else ""
            null_str = "NULL" if col["nullable"] else "NOT NULL"
            print(f"    - {col['name']}: {col['type']} {null_str}{pk_str}{fk_str}")

        if indexes:
            print("    Indexes:")
            for idx in indexes:
                uniq_flag = " UNIQUE" if idx["unique"] else ""
                print(f"      * {idx['name']} ({', '.join(idx['columns'])}){uniq_flag}")

        if uniques:
            print("    Unique Constraints:")
            for uq in uniques:
                print(f"      * {uq['name']} ({', '.join(uq['columns'])})")

    # Verify Phase 05.5 invariants
    print("\n" + "=" * 70)
    print("PHASE 05.5 INVARIANTS CHECK")
    print("=" * 70)

    invariants = [
        (
            "Canonical Garment has no merchant_id",
            "merchant_id" not in metadata.tables["canonical_garments"].columns,
        ),
        (
            "Merchant Offer has merchant_product_id FK",
            "merchant_product_id" in metadata.tables["merchant_offers"].columns,
        ),
        (
            "Merchant Offer has source_id FK",
            "source_id" in metadata.tables["merchant_offers"].columns,
        ),
        (
            "Merchant Offer has status and availability",
            "status" in metadata.tables["merchant_offers"].columns
            and "availability" in metadata.tables["merchant_offers"].columns,
        ),
        ("Price History table exists", "merchant_offer_price_history" in metadata.tables),
        ("Size Definitions table exists", "size_definitions" in metadata.tables),
        ("Product Variants table exists", "product_variants" in metadata.tables),
        ("Merchant Offer Sizes table exists", "merchant_offer_sizes" in metadata.tables),
        (
            "Catalog Provenance Records table exists",
            "catalog_provenance_records" in metadata.tables,
        ),
        (
            "Freshness timestamps exist on Merchant Offer",
            all(
                c in metadata.tables["merchant_offers"].columns
                for c in [
                    "last_seen_at",
                    "last_verified_at",
                    "last_price_verified_at",
                    "last_availability_verified_at",
                ]
            ),
        ),
        (
            "Takedown status exists on Offer and Product",
            "takedown_status" in metadata.tables["merchant_offers"].columns
            and "takedown_status" in metadata.tables["merchant_products"].columns,
        ),
    ]

    all_ok = True
    for desc, passed in invariants:
        status = "[PASS]" if passed else "[FAIL]"
        if not passed:
            all_ok = False
        print(f"  {status} {desc}")

    print("=" * 70)
    schema_report["all_invariants_passed"] = all_ok
    return schema_report


if __name__ == "__main__":
    report = inspect_catalog_schema()
    sys.exit(0 if report.get("all_invariants_passed") else 1)
