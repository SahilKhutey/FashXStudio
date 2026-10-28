#!/usr/bin/env python3
"""Import and ingest an apparel catalog CSV through FashXStudio's canonical pipeline.

Validates CSV schema, enforces catalog source clearance, persists products/offers/images,
and generates a structured ingestion report.

Usage:
    python scripts/catalog/import_catalog_csv.py data/catalog/catalog_seed.csv --dry-run
    python scripts/catalog/import_catalog_csv.py data/catalog/catalog_seed.csv --apply
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import CatalogSource, Merchant
from fashx.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from fashx.catalog.quality.quality_gate import CatalogQualityGate
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.database import get_session_factory
from scripts.catalog.validate_catalog_csv import validate_catalog_csv


def extract_attributes(row: dict[str, str]) -> dict[str, str]:
    """Extract standard fashion attributes from title and description for quality gate audit."""
    text = f"{row.get('title', '')} {row.get('subcategory', '')} {row.get('description', '')}".lower()

    dominant_color = "multi"
    for col in CatalogQualityGate.VALID_COLORS:
        if col in text:
            dominant_color = col
            break

    silhouette = "regular"
    for sil in CatalogQualityGate.VALID_SILHOUETTES:
        if sil in text:
            silhouette = sil
            break

    return {"silhouette": silhouette, "dominant_color": dominant_color}


@dataclass
class ImportReport:
    total_rows: int = 0
    inserted: int = 0
    updated: int = 0
    rejected: int = 0
    skipped: int = 0
    rejection_reasons: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    quality_passed: bool = False
    quality_score: float = 0.0

    def print_summary(self, apply: bool) -> None:
        mode_label = "APPLY (Production writes committed)" if apply else "DRY-RUN (No database writes committed)"
        print("=" * 60)
        print(f"CATALOG IMPORT REPORT [{mode_label}]")
        print("=" * 60)
        print(f"Total Rows Processed : {self.total_rows}")
        print(f"Products Inserted    : {self.inserted}")
        print(f"Products Updated     : {self.updated}")
        print(f"Products Rejected    : {self.rejected}")
        print(f"Products Skipped     : {self.skipped}")
        print(f"Quality Gate Status  : {'PASSED' if self.quality_passed else 'FAILED'} (Completeness: {self.quality_score:.1%})")
        if self.rejection_reasons:
            print("\nRejection Breakdown:")
            for reason, count in self.rejection_reasons.items():
                print(f"  - {reason}: {count}")
        print("=" * 60)


async def build_session_factory(db_url: str | None = None) -> async_sessionmaker[AsyncSession]:
    if db_url:
        engine_kwargs: dict[str, Any] = {}
        if "sqlite" in db_url:
            engine_kwargs["poolclass"] = StaticPool
        engine = create_async_engine(db_url, **engine_kwargs)
        if "sqlite" in db_url:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        return async_sessionmaker(engine, expire_on_commit=False)
    return get_session_factory()


async def import_catalog_csv(
    csv_path: Path,
    apply: bool = False,
    db_url: str | None = None,
    auto_register_source: bool = False,
) -> ImportReport:
    report = ImportReport()

    # 1. Structural pre-validation
    errors = validate_catalog_csv(csv_path)
    if errors:
        print(f"Validation failed before import: {len(errors)} error(s).", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
            report.rejected += 1
            report.rejection_reasons["csv_validation_failure"] += 1
        return report

    # 2. Read rows
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    report.total_rows = len(rows)

    try:
        session_factory = await build_session_factory(db_url)
    except Exception as exc:
        print(f"Error configuring database session: {exc}", file=sys.stderr)
        report.rejected = len(rows)
        report.rejection_reasons["db_connection_error"] = len(rows)
        return report

    uow = CatalogUnitOfWork(session_factory)
    items_for_audit: list[dict[str, Any]] = []

    try:
        async with uow:
            # Cache sources and merchants
            sources_by_slug: dict[str, CatalogSource] = {}
            merchants_by_name: dict[str, Merchant] = {}

            for row in rows:
                source_slug = row["source_slug"].strip()

                # Resolve source
                if source_slug not in sources_by_slug:
                    source = await uow.sources.get_by_slug(source_slug)
                    if source is None:
                        if auto_register_source:
                            source = CatalogSource(
                                slug=source_slug,
                                name=source_slug.replace("-", " ").title(),
                                kind="manual",
                                status="cleared",
                                rights_display=True,
                                rights_tryon=True,
                                image_policy="mirror",
                            )
                            uow.sources.add(source)
                            await uow.sources.flush()
                        else:
                            report.rejected += 1
                            report.rejection_reasons[f"unregistered_source_{source_slug}"] += 1
                            print(f"Error: Catalog source '{source_slug}' is not registered.", file=sys.stderr)
                            continue
                    sources_by_slug[source_slug] = source

                source = sources_by_slug[source_slug]

                # Require cleared status for production feed eligibility
                if source.status != "cleared" and apply:
                    report.rejected += 1
                    report.rejection_reasons[f"source_not_cleared_{source_slug}"] += 1
                    print(
                        f"Rejected '{row['source_product_id']}': Source '{source_slug}' status is '{source.status}'. "
                        "Sources must be cleared before ingestion into production.",
                        file=sys.stderr,
                    )
                    continue

                # Resolve merchant
                merchant_name = row.get("brand", "").strip() or source.name
                if merchant_name not in merchants_by_name:
                    merchant = await uow.merchants.get_by_name(merchant_name)
                    if merchant is None:
                        merchant = Merchant(name=merchant_name, merchant_type="brand")
                        uow.merchants.add(merchant)
                        await uow.merchants.flush()
                    merchants_by_name[merchant_name] = merchant
                merchant = merchants_by_name[merchant_name]

                # Check existing product for insert vs update counting
                existing_prod = await uow.merchant_products.get_by_source_id(
                    merchant.id, row["source_product_id"].strip()
                )
                is_update = existing_prod is not None

                # Prepare command
                price_minor = int(row["price_minor"].strip())
                in_stock = row["in_stock"].strip().lower() in {"true", "1", "yes"}
                tryon_rights = row["tryon_rights"].strip().lower() in {"true", "1", "yes"}
                sizes = [s.strip() for s in row.get("size_values", "").split("|") if s.strip()]

                cmd = IngestProductCommand(
                    merchant_id=merchant.id,
                    source_id=source.id,
                    source_product_id=row["source_product_id"].strip(),
                    title=row["title"].strip(),
                    source_url=row["product_url"].strip(),
                    category=row["category"].strip(),
                    subcategory=row.get("subcategory", "").strip() or None,
                    description=row.get("description", "").strip() or None,
                    price_minor=price_minor,
                    currency=row["currency"].strip(),
                    in_stock=in_stock,
                    sizes_in_stock=sizes,
                    image_url=row.get("image_url", "").strip() or None,
                    image_rights=row.get("image_rights", "").strip() or None,
                    tryon_rights=tryon_rights,
                )

                # Execute domain use case to validate & simulate persistence
                use_case = IngestMerchantProductUseCase(uow)
                await use_case.execute(cmd)

                if is_update:
                    report.updated += 1
                else:
                    report.inserted += 1

                # Prepare items for quality audit
                extracted_attrs = extract_attributes(row)
                items_for_audit.append(
                    {
                        "category": cmd.category,
                        "attributes": extracted_attrs,
                        "price_minor": cmd.price_minor,
                        "in_stock": cmd.in_stock,
                        "source_status": source.status,
                        "image_url": cmd.image_url,
                        "image_rights": cmd.image_rights,
                    }
                )

            if apply:
                await uow.commit()

    except (OSError, ConnectionRefusedError) as conn_err:
        print(
            f"Database connection error: {conn_err}.\n"
            "If PostgreSQL is not running locally, pass --db-url sqlite+aiosqlite:///:memory: --auto-register-source for local execution.",
            file=sys.stderr,
        )
        report.rejected = len(rows)
        report.rejection_reasons["postgres_connection_refused"] = len(rows)
        return report

    # 3. Catalog quality evaluation
    quality_report = CatalogQualityGate.audit_garment_batch(items_for_audit)
    report.quality_passed = quality_report.passed_gate
    report.quality_score = quality_report.completeness_score

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Import catalog CSV into FashXStudio")
    parser.add_argument("csv_path", type=Path, help="Path to apparel catalog CSV")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Validate and simulate ingestion without committing writes")
    group.add_argument("--apply", action="store_true", help="Execute ingestion and commit database writes")
    parser.add_argument("--db-url", type=str, default=None, help="Database connection URL (defaults to DATABASE_URL)")
    parser.add_argument(
        "--auto-register-source",
        action="store_true",
        help="In testing/dry-run, auto-register cleared source if not found in database",
    )

    args = parser.parse_args()
    report = asyncio.run(
        import_catalog_csv(
            args.csv_path,
            apply=args.apply,
            db_url=args.db_url,
            auto_register_source=args.auto_register_source,
        )
    )
    report.print_summary(apply=args.apply)

    if report.rejected > 0 or not report.quality_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
