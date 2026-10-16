"""CLI tool and script to backfill tryon_supported on canonical garments.

Backfills canonical garments to tryon_supported = True when:
  1. Associated catalog source is 'cleared'
  2. Source rights_tryon is True
  3. Source image_policy is 'mirror'
  4. Garment category is in supported categories (tops, bottoms, one-pieces, etc.)

Usage:
    python scripts/catalog/backfill_tryon_supported.py
"""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from fashx.core.database import get_session_factory

BACKFILL_SQL = """
UPDATE canonical_garments
SET tryon_supported = TRUE
WHERE id IN (
    SELECT mo.garment_id
    FROM merchant_offers mo
    JOIN merchant_products mp
        ON mo.merchant_id = mp.merchant_id AND mo.source_product_id = mp.source_product_id
    JOIN catalog_sources cs
        ON mp.source_id = cs.id
    WHERE cs.status = 'cleared'
      AND cs.rights_tryon = TRUE
      AND cs.image_policy = 'mirror'
)
AND lower(category) IN ('tops', 'bottoms', 'one-pieces', 'top', 'bottom', 'one_piece')
"""


async def backfill_tryon_supported(session: AsyncSession) -> int:
    """Execute tryon_supported backfill query on session and return affected row count."""
    res: Any = await session.execute(text(BACKFILL_SQL))
    rc = getattr(res, "rowcount", 0)
    return rc if isinstance(rc, int) and rc >= 0 else 0


async def main() -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        updated = await backfill_tryon_supported(session)
        await session.commit()
        print(f"Successfully backfilled tryon_supported: {updated} garments updated.")


if __name__ == "__main__":
    asyncio.run(main())
