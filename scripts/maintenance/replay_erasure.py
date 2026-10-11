"""Replay account erasure for all tombstoned users following a database restore.

Ensures no erased accounts or biometric objects are resurrected from restored backups.
"""

import asyncio
import logging
import sys
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from database.models.erasure import ErasureTombstone
from fashx.application.erasure import erase_account
from fashx.core.dependencies import get_storage
from fashx.core.settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("replay_erasure")


class SimpleUnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()


async def replay_erasure_tombstones() -> int:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    storage = get_storage(settings)

    replayed = 0
    errors = 0

    async with AsyncSession(engine) as session:
        stmt = select(ErasureTombstone.user_id)
        result = await session.execute(stmt)
        user_ids = [row[0] for row in result.all()]

        logger.info("Found %d tombstone(s) to replay", len(user_ids))

        for uid in user_ids:
            try:
                uow = SimpleUnitOfWork(session)
                res = await erase_account(uow, uid, storage=storage)
                await session.commit()
                replayed += 1
                logger.info("Replayed erasure for user %s (%s)", uid, res.get("status"))
            except Exception as e:
                errors += 1
                await session.rollback()
                logger.error("Failed to replay erasure for user %s: %s", uid, e)

    await engine.dispose()
    logger.info("Replay completed. Successfully replayed: %d, Errors: %d", replayed, errors)
    return replayed


if __name__ == "__main__":
    count = asyncio.run(replay_erasure_tombstones())
    sys.exit(0)
