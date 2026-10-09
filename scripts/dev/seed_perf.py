import asyncio
import random
import time
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from database.models.catalog import CanonicalGarment, GarmentEnrichment, Merchant, MerchantOffer, MerchantProduct
from fashx.core.settings import get_settings


async def seed_garments(count: int = 1000) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    print(f"Connecting to {settings.database_url}...")
    categories = ["tops", "bottoms", "dresses", "outerwear", "shoes"]
    colors = ["black", "navy", "white", "beige", "red", "green"]

    async with factory() as session:
        merchant = Merchant(id=uuid4(), name=f"PerfMerchant-{uuid4().hex[:6]}", merchant_type="brand")
        session.add(merchant)
        await session.flush()

        print(f"Seeding {count} garments and offers...")
        start_time = time.time()
        for i in range(count):
            garment_id = uuid4()
            cat = random.choice(categories)
            garment = CanonicalGarment(
                id=garment_id,
                category=cat,
                subcategory="casual",
            )
            session.add(garment)

            mp = MerchantProduct(
                id=uuid4(),
                merchant_id=merchant.id,
                source_product_id=f"PERF-{i}",
                title=f"Sample Garment {i}",
                source_url=f"https://perf.test/items/{i}",
            )
            session.add(mp)

            offer = MerchantOffer(
                id=uuid4(),
                garment_id=garment_id,
                merchant_id=merchant.id,
                source_product_id=f"PERF-{i}",
                url=f"https://perf.test/items/{i}",
                price_minor=random.randint(49900, 999900),
                currency="INR",
            )
            session.add(offer)

            enrichment = GarmentEnrichment(
                garment_id=garment_id,
                category=cat,
                dominant_color=random.choice(colors),
                silhouette="regular",
                formality="casual",
                embedding=[random.uniform(-1.0, 1.0) for _ in range(512)],
            )
            session.add(enrichment)

            if (i + 1) % 200 == 0:
                await session.flush()
                print(f"  Flushed {i + 1}/{count} garments...")

        await session.commit()
        duration = time.time() - start_time
        print(f"Seeded {count} garments in {duration:.2f}s ({count / duration:.1f} garments/sec)")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_garments(count=1000))
