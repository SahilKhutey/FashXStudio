from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text

logger = logging.getLogger("fashx.application.retention")


async def cleanup_unsaved_tryons(
    session: Any,
    storage: Any | None = None,
    cutoff_days: int = 30,
    batch_size: int = 500,
) -> dict[str, int]:
    """Prune unsaved tryon jobs and artifacts older than cutoff_days (Rule 9.7).

    If an artifact was saved to wardrobe (referenced in wardrobe_items), it is preserved.
    """
    cutoff = datetime.now(UTC) - timedelta(days=cutoff_days)

    # 1. Query candidate artifacts not saved in wardrobe
    query_unreferenced = text(
        """
        SELECT a.id, a.job_id, a.result_key, a.artifact_key
        FROM tryon_artifacts a
        JOIN tryon_jobs j ON a.job_id = j.id
        WHERE j.created_at < :cutoff
          AND a.id NOT IN (
              SELECT tryon_artifact_id
              FROM wardrobe_items
              WHERE tryon_artifact_id IS NOT NULL
          )
        LIMIT :batch_limit
        """
    )

    result = await session.execute(query_unreferenced, {"cutoff": cutoff, "batch_limit": batch_size})
    rows = result.fetchall()

    deleted_keys_count = 0
    deleted_jobs_count = 0

    if rows:
        job_ids = [row[1] for row in rows]
        storage_keys = []
        for row in rows:
            if row[2]:  # result_key
                storage_keys.append(row[2])
            if row[3]:  # artifact_key
                storage_keys.append(row[3])

        # Delete objects from object store first
        if storage is not None:
            for k in storage_keys:
                try:
                    if hasattr(storage, "delete"):
                        storage.delete(k)
                    deleted_keys_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete S3 object {k}: {e}")

        # Delete tryon_jobs rows (cascades to tryon_artifacts)
        del_stmt = text(
            """
            DELETE FROM tryon_jobs
            WHERE id = ANY(:job_ids)
            """
        )
        del_result = await session.execute(del_stmt, {"job_ids": job_ids})
        deleted_jobs_count = getattr(del_result, "rowcount", len(job_ids))

    # Also clean up failed or aborted tryon_jobs older than cutoff that never generated artifacts
    orphan_jobs_del = text(
        """
        DELETE FROM tryon_jobs
        WHERE created_at < :cutoff
          AND status IN ('failed', 'expired', 'cancelled')
          AND id NOT IN (SELECT job_id FROM tryon_artifacts)
        """
    )
    res_orphan = await session.execute(orphan_jobs_del, {"cutoff": cutoff})
    deleted_jobs_count += getattr(res_orphan, "rowcount", 0)

    return {
        "tryon_jobs_deleted": deleted_jobs_count,
        "storage_keys_purged": deleted_keys_count,
    }


async def cleanup_impressions(
    session: Any,
    cutoff_days: int = 90,
    batch_size: int = 500,
) -> int:
    """Delete raw feed impression logs older than cutoff_days (Rule 9.7)."""
    cutoff = datetime.now(UTC) - timedelta(days=cutoff_days)
    del_stmt = text(
        """
        DELETE FROM feed_impressions
        WHERE id IN (
            SELECT id FROM feed_impressions
            WHERE created_at < :cutoff
            LIMIT :batch_limit
        )
        """
    )
    result = await session.execute(del_stmt, {"cutoff": cutoff, "batch_limit": batch_size})
    deleted_count = getattr(result, "rowcount", 0)
    return deleted_count


async def anonymize_analytics(
    session: Any,
    cutoff_days: int = 365,
    batch_size: int = 500,
) -> int:
    """Anonymize analytics and domain events older than 12 months (DPDP / CERT-In compliance)."""
    cutoff = datetime.now(UTC) - timedelta(days=cutoff_days)
    update_stmt = text(
        """
        UPDATE domain_events
        SET user_id = NULL
        WHERE id IN (
            SELECT id FROM domain_events
            WHERE occurred_at < :cutoff
              AND user_id IS NOT NULL
            LIMIT :batch_limit
        )
        """
    )
    result = await session.execute(update_stmt, {"cutoff": cutoff, "batch_limit": batch_size})
    anonymized_count = getattr(result, "rowcount", 0)
    return anonymized_count


async def run_daily_retention(
    session: Any,
    storage: Any | None = None,
) -> dict[str, Any]:
    """Execute nightly retention cleanup suite and emit structured metrics."""
    logger.info("Starting daily retention cleanup run")

    tryon_summary = await cleanup_unsaved_tryons(session, storage=storage, cutoff_days=30)
    impressions_count = await cleanup_impressions(session, cutoff_days=90)
    analytics_count = await anonymize_analytics(session, cutoff_days=365)

    summary = {
        "status": "success",
        "timestamp": datetime.now(UTC).isoformat(),
        "tryon_jobs_deleted": tryon_summary["tryon_jobs_deleted"],
        "storage_keys_purged": tryon_summary["storage_keys_purged"],
        "impressions_deleted": impressions_count,
        "analytics_events_anonymized": analytics_count,
    }

    logger.info(f"Daily retention cleanup completed: {summary}")
    return summary
