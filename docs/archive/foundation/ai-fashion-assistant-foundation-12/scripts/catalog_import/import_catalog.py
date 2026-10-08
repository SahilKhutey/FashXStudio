"""Import curated MVP catalog records into the canonical catalog contract.

Usage in a configured environment:
    python -m scripts.catalog_import.import_catalog --file scripts/catalog_import/catalog_fixture.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.app.catalog.application.catalog_use_cases import CatalogApplicationService
from api.app.catalog.repositories.catalog import CatalogRepository
from api.app.core.settings import get_settings
from schemas.catalog.garment_image import GarmentImageCreate
from schemas.catalog.intake import CatalogIntakeRequest


async def run(path: Path) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Importing through the application service preserves the same invariants as live intake.
    async with session_factory() as session:
        repository = CatalogRepository(session)
        service = CatalogApplicationService(repository)
        records = json.loads(path.read_text(encoding="utf-8"))

        for record in records:
            brand, _ = await repository.get_or_create_brand(name=record["brand_name"])
            merchant, _ = await repository.get_or_create_merchant(
                name=record["merchant_name"], merchant_type=record["merchant_type"]
            )
            payload = CatalogIntakeRequest(
                merchant_id=merchant.id,
                brand_id=brand.id,
                source_product_id=record["source_product_id"],
                title=record["title"],
                description=record.get("description"),
                source_url=record["source_url"],
                category=record["category"],
                subcategory=record.get("subcategory"),
                price_minor=record["price_minor"],
                currency=record.get("currency", "INR"),
                images=[GarmentImageCreate(**image) for image in record.get("images", [])],
            )
            result = await service.intake_listing(payload)
            print(
                f"{record['source_product_id']}: {result.operation} "
                f"garment={result.product_id} images={result.image_count}"
            )

    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(run(args.file))


if __name__ == "__main__":
    main()
