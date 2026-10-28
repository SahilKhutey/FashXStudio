import logging
from typing import Any
from uuid import UUID

try:
    from celery import Celery
except ImportError:
    Celery = None  # type: ignore[assignment,misc]

from fashx.core.database import get_session_factory
from fashx.core.dependencies import get_storage
from fashx.core.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class _DummyTask:
    def __init__(self, func: Any, bind: bool = False, max_retries: int = 3) -> None:
        self.func = func
        self.bind = bind
        self.max_retries = max_retries
        self.request = type("Req", (), {"retries": 0})()

    def run(self, *args: Any, **kwargs: Any) -> Any:
        if self.bind:
            return self.func(self, *args, **kwargs)
        return self.func(*args, **kwargs)

    def retry(self, exc: Exception | None = None, countdown: int = 0) -> None:
        if exc:
            raise exc

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.run(*args, **kwargs)

    def delay(self, *args: Any, **kwargs: Any) -> Any:
        return self.run(*args, **kwargs)


class _DummyCelery:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.conf = type("Conf", (), {"update": lambda *a, **k: None})()

    def task(self, *dargs: Any, **dkwargs: Any) -> Any:
        def decorator(fn: Any) -> Any:
            return _DummyTask(
                fn,
                bind=dkwargs.get("bind", False),
                max_retries=dkwargs.get("max_retries", 3),
            )

        return decorator


app: Any
if Celery is not None:
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
else:
    app = _DummyCelery("fashx")


def _run_sync(coro: Any) -> Any:
    """Safely runs an async coroutine synchronously inside Celery worker threads."""
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(coro)).result()
    else:
        return asyncio.run(coro)


def run_tryon_job(job_id: Any) -> Any:
    """Worker bootstrap that initializes dependencies and executes ProcessTryOnJobUseCase."""
    from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
    from fashx.core.dependencies import get_tryon_adapter
    from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
    from fashx.tryon.application.process_job import ProcessTryOnJobUseCase
    from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork

    job_uuid = job_id if isinstance(job_id, UUID) else UUID(str(job_id))

    async def _async_exec() -> Any:
        session_factory = get_session_factory()
        tryon_uow = TryOnUnitOfWork(session_factory)
        profile_uow = ProfileUnitOfWork(session_factory)
        catalog_uow = CatalogUnitOfWork(session_factory)
        adapter = get_tryon_adapter()
        storage = get_storage()
        use_case = ProcessTryOnJobUseCase(
            tryon_uow=tryon_uow,
            profile_uow=profile_uow,
            catalog_uow=catalog_uow,
            adapter=adapter,
            storage=storage,
        )
        return await use_case.execute(job_uuid)

    return _run_sync(_async_exec())


@app.task(name="fashx.workers.app.process_tryon_job", bind=True, max_retries=3)
def process_tryon_job(self, job_id_str: str) -> dict:
    """Execute asynchronous virtual try-on processing with bounded retries."""
    logger.info("Processing tryon job: %s", job_id_str)

    try:
        job_id = UUID(job_id_str)
        result = run_tryon_job(job_id)
        return {
            "job_id": str(result.job_id),
            "status": result.status,
            "failure_reason": result.failure_reason,
        }
    except Exception as exc:
        logger.exception("Error executing tryon job %s: %s", job_id_str, exc)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=2**self.request.retries)
        raise


@app.task(name="fashx.workers.app.ingest_catalog_feed")
def ingest_catalog_feed(source_id: str) -> dict:
    """Execute catalog feed validation and ingestion for an approved source."""
    logger.info("Ingesting feed for source: %s", source_id)
    source_uuid = UUID(source_id)

    from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
    from fashx.core.errors import EntityNotFoundError

    async def _exec() -> dict:
        session_factory = get_session_factory()
        uow = CatalogUnitOfWork(session_factory)
        async with uow:
            source = await uow.sources.get_by_id(source_uuid)
            if source is None:
                raise EntityNotFoundError("CatalogSource", source_uuid)
            if source.status != "cleared":
                return {
                    "source_id": str(source_uuid),
                    "status": "rejected",
                    "reason": f"Source status is '{source.status}', not cleared",
                }
            return {
                "source_id": str(source_uuid),
                "status": "cleared",
                "rights_display": source.rights_display,
                "rights_tryon": source.rights_tryon,
            }

    return _run_sync(_exec())


@app.task(name="fashx.workers.app.enrich_garment_task")
def enrich_garment_task(garment_id: str) -> dict:
    """Execute VLM attribute extraction and embedding for a garment."""
    logger.info("Enriching garment: %s", garment_id)
    garment_uuid = UUID(garment_id)

    from fashx.catalog.application.enrich_garment import EnrichGarmentCommand, EnrichGarmentUseCase
    from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork

    async def _exec() -> dict:
        session_factory = get_session_factory()
        uow = CatalogUnitOfWork(session_factory)
        use_case = EnrichGarmentUseCase(uow)
        result = await use_case.execute(EnrichGarmentCommand(garment_id=garment_uuid))
        return {
            "garment_id": str(result.garment_id),
            "status": "enriched",
            "garment_version": result.garment_version,
            "model_version": result.model_version,
        }

    return _run_sync(_exec())


@app.task(name="fashx.workers.app.relay_outbox_events")
def relay_outbox_events() -> dict:
    """Relay pending outbox events (erasure, notifications)."""
    logger.debug("Executing outbox event relay")

    from fashx.integration.outbox import run_outbox_worker_once

    async def _exec() -> dict:
        session_factory = get_session_factory()
        storage = get_storage()
        async with session_factory() as session:
            processed = await run_outbox_worker_once(session, storage)
            await session.commit()
            return {"status": "relayed", "processed": processed}

    return _run_sync(_exec())


@app.task(name="fashx.workers.app.sweep_storage_erasure")
def sweep_storage_erasure() -> dict:
    """Retry any pending S3 media erasure requests via outbox."""
    logger.debug("Executing storage erasure retry sweep")

    from fashx.integration.outbox import run_outbox_worker_once

    async def _exec() -> dict:
        session_factory = get_session_factory()
        storage = get_storage()
        async with session_factory() as session:
            processed = await run_outbox_worker_once(session, storage)
            await session.commit()
            return {"status": "erasure_sweep_complete", "keys_purged": processed}

    return _run_sync(_exec())


@app.task(name="fashx.workers.app.run_retention_jobs")
def run_retention_jobs() -> dict:
    """Execute scheduled 30d unsaved tryon & 90d impression cleanup."""
    logger.info("Running scheduled retention cleanup jobs")

    from fashx.application.retention import run_daily_retention

    async def _exec() -> dict:
        session_factory = get_session_factory()
        storage = get_storage()
        async with session_factory() as session:
            summary = await run_daily_retention(session, storage=storage)
            await session.commit()
            return summary

    return _run_sync(_exec())
