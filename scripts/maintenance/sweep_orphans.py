from __future__ import annotations

import argparse
import asyncio
import logging
from typing import Any

from sqlalchemy import select

from database.models.identity import UserPhoto
from database.models.media import MediaObject
from fashx.core.database import get_session_factory
from fashx.core.dependencies import get_storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sweep_orphans")


async def sweep_orphans(storage: Any | None = None, dry_run: bool = False) -> int:
    """Find and delete storage objects under u/ that have no corresponding database row."""
    if storage is None:
        storage = get_storage()

    # 1. Collect all known keys from database
    session_factory = get_session_factory()
    known_keys: set[str] = set()

    async with session_factory() as session:
        try:
            media_stmt = select(MediaObject.object_key)
            media_keys = (await session.scalars(media_stmt)).all()
            known_keys.update(media_keys)
        except Exception as e:
            logger.warning(f"Could not query media_objects: {e}")

        try:
            photo_stmt = select(UserPhoto.storage_key)
            photo_keys = (await session.scalars(photo_stmt)).all()
            known_keys.update([k for k in photo_keys if k])
        except Exception as e:
            logger.warning(f"Could not query user_photos: {e}")

    logger.info(f"Loaded {len(known_keys)} active media keys from database.")

    # 2. List all storage objects under u/
    stored_keys = storage.list_prefix("u/")
    logger.info(f"Found {len(stored_keys)} objects under prefix 'u/' in storage.")

    orphans = [k for k in stored_keys if k not in known_keys]
    logger.info(f"Identified {len(orphans)} orphaned objects.")

    deleted_count = 0
    for key in orphans:
        if dry_run:
            logger.info(f"[DRY-RUN] Would delete orphan: {key}")
        else:
            logger.info(f"Deleting orphan: {key}")
            try:
                storage.delete(key)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete {key}: {e}")

    logger.info(f"Sweep complete. Removed {deleted_count} orphans.")
    return deleted_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Sweep orphaned object storage files.")
    parser.add_argument("--dry-run", action="store_true", help="Print orphans without deleting them.")
    args = parser.parse_args()

    asyncio.run(sweep_orphans(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
