"""Backfill and normalize sizes_in_stock on canonical garments."""

import asyncio
import logging

from database.session import get_session_factory
from sqlalchemy import select, update

from database.models.catalog import CanonicalGarment, SizeMeasurement

logger = logging.getLogger(__name__)

DEFAULT_SIZES = ["S", "M", "L", "XL"]


async def backfill_sizes() -> int:
    """Backfill sizes_in_stock for canonical garments missing size arrays."""
    session_factory = get_session_factory()
    updated_count = 0

    async with session_factory() as session:
        # 1. Fetch distinct size measurements per garment
        meas_stmt = select(SizeMeasurement.garment_id, SizeMeasurement.size_label).distinct()
        meas_res = await session.execute(meas_stmt)
        garment_to_sizes: dict = {}
        for g_id, s_lbl in meas_res:
            garment_to_sizes.setdefault(g_id, set()).add(s_lbl)

        # 2. Update canonical garments
        stmt = select(CanonicalGarment)
        res = await session.execute(stmt)
        garments = res.scalars().all()

        for g in garments:
            if not g.sizes_in_stock:
                sizes = sorted(garment_to_sizes.get(g.id, DEFAULT_SIZES))
                await session.execute(
                    update(CanonicalGarment)
                    .where(CanonicalGarment.id == g.id)
                    .values(sizes_in_stock=sizes)
                )
                updated_count += 1

        await session.commit()

    logger.info("Backfilled %d canonical garments with sizes_in_stock", updated_count)
    return updated_count


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    try:
        count = asyncio.run(backfill_sizes())
        print(f"Successfully backfilled {count} garments.")
    except Exception as e:
        print(f"Backfill skipped (database offline or not connected): {e}")


if __name__ == "__main__":
    main()
