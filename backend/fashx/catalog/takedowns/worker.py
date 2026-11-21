from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import MerchantProduct
from database.models.catalog_auth import CatalogTakedownRequest

logger = logging.getLogger(__name__)


class TakedownAsyncWorker:
    """Async worker handling cascading asset unpublishing and cache invalidation."""

    @classmethod
    async def process_unpublishing(
        cls, session: AsyncSession, takedown_id: UUID, source_id: UUID
    ) -> int:
        # Mark merchant products from this source as suspended
        stmt = (
            update(MerchantProduct)
            .where(MerchantProduct.source_id == source_id)
            .values(status="suspended")
        )
        res = await session.execute(stmt)
        affected_count = res.rowcount

        # Update takedown counts
        td_stmt = (
            update(CatalogTakedownRequest)
            .where(CatalogTakedownRequest.id == takedown_id)
            .values(affected_product_count=affected_count)
        )
        await session.execute(td_stmt)
        await session.flush()

        logger.info(
            f"Takedown worker processed unpublishing for source {source_id}: "
            f"{affected_count} products deactivated."
        )
        return affected_count
