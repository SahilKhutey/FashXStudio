#!/usr/bin/env python3
"""CLI tool to synchronize external store catalog sources into FashXStudio.

Usage:
    python scripts/catalog/sync_sources.py --source partner-feed --dry-run
    python scripts/catalog/sync_sources.py --source amazon --apply
    python scripts/catalog/sync_sources.py --all --dry-run
    python scripts/catalog/sync_sources.py --reconcile-stale --max-age-hours 48 --apply
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import CatalogSource
from fashx.catalog.acquisition.adapters import (
    AmazonAdapter,
    FlipkartAdapter,
    MyntraAdapter,
    PartnerFeedAdapter,
)
from fashx.catalog.acquisition.contract import SourceProduct
from fashx.catalog.acquisition.registry import AdapterRegistry, SourceConfig
from fashx.catalog.acquisition.sync_service import CatalogSyncService
from fashx.core.database import get_session_factory


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


def build_default_registry() -> AdapterRegistry:
    registry = AdapterRegistry()

    # 1. Partner feed adapter with canonical seed
    partner_adapter = PartnerFeedAdapter(
        config=SourceConfig(
            source_slug="manual-demo",
            name="Manual Demo Wardrobe",
            kind="manual",
            image_policy="mirror",
        ),
        feed_csv_path=Path("data/catalog/catalog_seed.csv"),
    )
    registry.register(partner_adapter)

    # 2. Amazon adapter with sample authorized items
    amazon_items = [
        SourceProduct(
            source_slug="amazon",
            source_product_id="B09XYZ1234",
            title="Amazon Brand - Symbol Men Formal Shirt",
            brand="Symbol",
            category="tops",
            subcategory="shirt",
            description="Regular fit cotton button down shirt; sky blue",
            price_minor=89900,
            currency="INR",
            product_url="https://www.amazon.in/dp/B09XYZ1234",
            image_url="https://images.fashx.studio/products/amazon-shirt-01.jpg",
            in_stock=True,
            sizes=("S", "M", "L", "XL"),
            image_rights="partner_authorized",
            tryon_rights=False,
        ),
        SourceProduct(
            source_slug="amazon",
            source_product_id="B09XYZ5678",
            title="Amazon Brand - Inkast Denim Men Slim Jeans",
            brand="Inkast",
            category="bottoms",
            subcategory="jeans",
            description="Mid-rise slim fit stretch denim; dark indigo",
            price_minor=129900,
            currency="INR",
            product_url="https://www.amazon.in/dp/B09XYZ5678",
            image_url="https://images.fashx.studio/products/amazon-jeans-01.jpg",
            in_stock=True,
            sizes=("30", "32", "34", "36"),
            image_rights="partner_authorized",
            tryon_rights=False,
        ),
    ]
    amazon_adapter = AmazonAdapter(feed_items=amazon_items)
    registry.register(amazon_adapter)

    # 3. Myntra adapter with sample authorized items
    myntra_items = [
        SourceProduct(
            source_slug="myntra",
            source_product_id="MYN-987654",
            title="Roadster Men Pure Cotton Casual Shirt",
            brand="Roadster",
            category="tops",
            subcategory="shirt",
            description="Sustainable cotton casual overshirt; olive green",
            price_minor=109900,
            currency="INR",
            product_url="https://www.myntra.com/shirts/roadster/987654/buy",
            image_url="https://images.fashx.studio/products/myntra-shirt-01.jpg",
            in_stock=True,
            sizes=("M", "L", "XL"),
            image_rights="partner_authorized",
            tryon_rights=False,
        )
    ]
    myntra_adapter = MyntraAdapter(feed_items=myntra_items)
    registry.register(myntra_adapter)

    # 4. Flipkart adapter with sample authorized items
    flipkart_items = [
        SourceProduct(
            source_slug="flipkart",
            source_product_id="FLIP-554433",
            title="Metronaut Men Solid Bomber Jacket",
            brand="Metronaut",
            category="outerwear",
            subcategory="jacket",
            description="Full sleeve zip-front utility bomber jacket; black",
            price_minor=179900,
            currency="INR",
            product_url="https://www.flipkart.com/metronaut-jacket/p/itm554433",
            image_url="https://images.fashx.studio/products/flipkart-jacket-01.jpg",
            in_stock=True,
            sizes=("S", "M", "L"),
            image_rights="partner_authorized",
            tryon_rights=False,
        )
    ]
    flipkart_adapter = FlipkartAdapter(feed_items=flipkart_items)
    registry.register(flipkart_adapter)

    return registry


async def ensure_source_registered(
    session_factory: async_sessionmaker[AsyncSession],
    source_slug: str,
    name: str,
) -> None:
    async with session_factory() as session:
        from sqlalchemy import select
        stmt = select(CatalogSource).where(CatalogSource.slug == source_slug)
        existing = (await session.scalars(stmt)).first()
        if existing is None:
            source = CatalogSource(
                slug=source_slug,
                name=name,
                kind="api" if source_slug in {"amazon", "myntra", "flipkart"} else "feed_url",
                status="cleared",
                rights_display=True,
                rights_tryon=False,
                image_policy="mirror",
            )
            session.add(source)
            await session.commit()


async def run_sync(args: argparse.Namespace) -> None:
    session_factory = await build_session_factory(args.db_url)
    registry = build_default_registry()
    service = CatalogSyncService(session_factory=session_factory, registry=registry)

    # If auto-register is requested or sqlite in-memory testing
    if args.auto_register_sources or (args.db_url and "sqlite" in args.db_url):
        for slug in registry.list_sources():
            await ensure_source_registered(
                session_factory,
                slug,
                slug.replace("-", " ").title(),
            )

    if args.reconcile_stale:
        stale_count = await service.reconcile_stale_offers(
            source_slug=args.source if args.source != "all" else None,
            stale_threshold_hours=args.max_age_hours,
            apply=args.apply,
        )
        mode = "APPLY" if args.apply else "DRY-RUN"
        print(f"Stale Reconciliation [{mode}]: {stale_count} stale offer(s) marked out of stock.")
        return

    if args.all or args.source == "all":
        reports = await service.sync_all_sources(limit_per_source=args.limit, apply=args.apply)
        for _slug, rep in reports.items():
            rep.print_summary(apply=args.apply)
    else:
        rep = await service.sync_source(args.source, limit=args.limit, apply=args.apply)
        rep.print_summary(apply=args.apply)
        if not rep.success:
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronize catalog sources into FashXStudio")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source", type=str, help="Specific source slug to sync (or 'all')")
    group.add_argument("--all", action="store_true", help="Sync all registered source adapters")
    group.add_argument("--reconcile-stale", action="store_true", help="Reconcile out-of-date offers")

    parser.add_argument("--limit", type=int, default=100, help="Max items per source batch")
    parser.add_argument("--max-age-hours", type=int, default=48, help="Threshold hours for stale reconciliation")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--dry-run", action="store_true", help="Simulate without database writes")
    mode_group.add_argument("--apply", action="store_true", help="Commit database writes")

    parser.add_argument("--db-url", type=str, default=None, help="Database connection URL")
    parser.add_argument(
        "--auto-register-sources",
        action="store_true",
        help="In testing/dry-run, auto-register cleared sources if missing",
    )

    args = parser.parse_args()
    try:
        asyncio.run(run_sync(args))
    except (OSError, ConnectionRefusedError) as conn_err:
        print(
            f"Database connection error: {conn_err}.\n"
            "If PostgreSQL is not running locally, pass --db-url sqlite+aiosqlite:///:memory: for local execution.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
