import logging
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from database.models.operations import WorkerDeadLetter
from fashx.core.database import get_session_factory

logger = logging.getLogger(__name__)

SAFE_ARGUMENTS: dict[str, str] = {
    "fashx.workers.app.process_tryon_job": "job_id",
    "fashx.workers.app.ingest_catalog_feed": "source_id",
    "fashx.workers.app.enrich_garment_task": "garment_id",
}

PROHIBITED_SUBSTRINGS = (
    "bearer ",
    "x-amz-",
    "http://",
    "https://",
    "s3://",
)


def build_safe_payload(
    task_name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> dict[str, str]:
    """Persist only approved identifiers, strictly filtering out raw user or media data."""
    field = SAFE_ARGUMENTS.get(task_name)
    if not field:
        return {}
    value = kwargs.get(field)
    if value is None and args:
        value = args[0]
    if value is None:
        return {}

    val_str = str(value)
    # Prevent leaking presigned URLs or authorization headers
    val_lower = val_str.lower()
    if any(sub in val_lower for sub in PROHIBITED_SUBSTRINGS):
        return {}

    return {field: val_str}


async def _persist_dead_letter_async(
    task_id: str,
    task_name: str,
    queue_name: str,
    error_type: str,
    error_message: str,
    safe_payload: dict[str, Any],
    attempts: int = 0,
) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = select(WorkerDeadLetter).where(WorkerDeadLetter.task_id == task_id)
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is not None:
            record.error_type = error_type[:255]
            record.error_message = error_message[:1000]
            record.attempts = attempts
            record.safe_payload = safe_payload
        else:
            record = WorkerDeadLetter(
                id=uuid4(),
                task_id=task_id,
                task_name=task_name,
                queue_name=queue_name,
                error_type=error_type[:255],
                error_message=error_message[:1000],
                safe_payload=safe_payload,
                status="pending",
                attempts=attempts,
            )
            session.add(record)
        await session.commit()


def persist_dead_letter_sync(
    task_id: str,
    task_name: str,
    queue_name: str,
    error_type: str,
    error_message: str,
    safe_payload: dict[str, Any],
    attempts: int = 0,
) -> None:
    """Synchronously persist dead-letter records from Celery failure callbacks."""
    from fashx.workers.app import _run_sync

    try:
        _run_sync(
            _persist_dead_letter_async(
                task_id=task_id,
                task_name=task_name,
                queue_name=queue_name,
                error_type=error_type,
                error_message=error_message,
                safe_payload=safe_payload,
                attempts=attempts,
            )
        )
        logger.info("Persisted dead letter for task %s (%s)", task_id, task_name)
    except Exception as exc:
        logger.error(
            "CRITICAL: Failed to persist dead letter for task %s to PostgreSQL: %s",
            task_id,
            exc,
        )
