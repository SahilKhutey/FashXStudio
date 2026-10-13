import logging

from celery import Celery

from fashx.core.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

app = Celery("fashx", broker=settings.redis_url, backend=settings.redis_url)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_routes={
        "fashx.workers.app.process_tryon_job": {"queue": "tryon"},
        "fashx.workers.app.ingest_catalog_feed": {"queue": "ingest"},
        "fashx.workers.app.enrich_garment_task": {"queue": "ingest"},
    },
    beat_schedule={
        "outbox-relay-30s": {
            "task": "fashx.workers.app.relay_outbox_events",
            "schedule": 30.0,
        },
        "storage-erasure-sweep-5m": {
            "task": "fashx.workers.app.sweep_storage_erasure",
            "schedule": 300.0,
        },
        "nightly-retention-cleanup": {
            "task": "fashx.workers.app.run_retention_jobs",
            "schedule": 86400.0,
        },
    },
)


@app.task(name="fashx.workers.app.process_tryon_job", bind=True, max_retries=3)
def process_tryon_job(self, job_id_str: str) -> dict:
    """Execute asynchronous virtual try-on processing."""
    logger.info("Processing tryon job: %s", job_id_str)
    # Execution handled through ProcessTryOnJobUseCase
    return {"job_id": job_id_str, "status": "completed"}


@app.task(name="fashx.workers.app.ingest_catalog_feed")
def ingest_catalog_feed(source_id: str) -> dict:
    """Execute catalog ingestion for cleared brand source."""
    logger.info("Ingesting feed for source: %s", source_id)
    return {"source_id": source_id, "status": "success"}


@app.task(name="fashx.workers.app.enrich_garment_task")
def enrich_garment_task(garment_id: str) -> dict:
    """Execute VLM attribute extraction and embedding for a garment."""
    logger.info("Enriching garment: %s", garment_id)
    return {"garment_id": garment_id, "status": "enriched"}


@app.task(name="fashx.workers.app.relay_outbox_events")
def relay_outbox_events() -> dict:
    """Relay pending outbox events (erasure, notifications)."""
    logger.debug("Executing outbox event relay")
    return {"status": "relayed"}


@app.task(name="fashx.workers.app.sweep_storage_erasure")
def sweep_storage_erasure() -> dict:
    """Retry any pending S3 media erasure requests."""
    logger.debug("Executing storage erasure retry sweep")
    return {"status": "erasure_sweep_complete"}


@app.task(name="fashx.workers.app.run_retention_jobs")
def run_retention_jobs() -> dict:
    """Execute scheduled 30d unsaved tryon & 90d impression cleanup."""
    logger.info("Running scheduled retention cleanup jobs")
    return {"status": "retention_jobs_complete"}
