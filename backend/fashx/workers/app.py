import logging
from typing import Any
from uuid import UUID

try:
    from celery import Celery, Task
except ImportError:
    Celery = None  # type: ignore[assignment,misc]
    Task = object  # type: ignore[assignment,misc]

from fashx.core.database import get_session_factory
from fashx.core.dependencies import get_storage
from fashx.core.settings import get_settings
from fashx.workers.dead_letter import build_safe_payload, persist_dead_letter_sync
from fashx.workers.queue_config import TASK_QUEUES, TASK_ROUTES

logger = logging.getLogger(__name__)
settings = get_settings()


class _DummyTask:
    def __init__(
        self,
        func: Any,
        bind: bool = False,
        max_retries: int = 3,
        base: Any = None,
        name: str | None = None,
    ) -> None:
        self.func = func
        self.bind = bind
        self.max_retries = max_retries
        self.base = base
        self.name = name or getattr(func, "__name__", "dummy_task")
        self.request = type(
            "Req",
            (),
            {"retries": 0, "delivery_info": {"routing_key": "maintenance"}},
        )()

    def run(self, *args: Any, **kwargs: Any) -> Any:
        if self.bind:
            return self.func(self, *args, **kwargs)
        return self.func(*args, **kwargs)

    def retry(self, exc: Exception | None = None, countdown: int = 0) -> None:
        if exc:
            raise exc

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        einfo: Any,
    ) -> None:
        try:
            queue_name = "unknown"
            if hasattr(self.request, "delivery_info") and self.request.delivery_info:
                queue_name = self.request.delivery_info.get("routing_key", "unknown")
            safe_payload = build_safe_payload(self.name, args, kwargs)
            attempts = getattr(self.request, "retries", 0) + 1
            persist_dead_letter_sync(
                task_id=task_id,
                task_name=self.name,
                queue_name=queue_name,
                error_type=type(exc).__name__,
                error_message=str(exc),
                safe_payload=safe_payload,
                attempts=attempts,
            )
        except Exception as dlq_err:
            logger.exception(
                "Failed in dead-letter failure callback for %s: %s", task_id, dlq_err
            )

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.run(*args, **kwargs)

    def delay(self, *args: Any, **kwargs: Any) -> Any:
        return self.run(*args, **kwargs)

    def apply_async(self, args: Any = None, kwargs: Any = None, **options: Any) -> Any:
        args = args or ()
        kwargs = kwargs or {}
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
                base=dkwargs.get("base"),
                name=dkwargs.get("name"),
            )

        return decorator


if Celery is not None:

    class FashxTask(Task):  # type: ignore[misc]
        """Custom Celery task base class providing automated dead-letter persistence."""

        def on_failure(
            self,
            exc: Exception,
            task_id: str,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
            einfo: Any,
        ) -> None:
            try:
                delivery_info = getattr(self.request, "delivery_info", None) or {}
                queue_name = (
                    delivery_info.get("routing_key")
                    or delivery_info.get("exchange")
                    or "unknown"
                )
                safe_payload = build_safe_payload(self.name, args, kwargs)
                attempts = getattr(self.request, "retries", 0) + 1
                persist_dead_letter_sync(
                    task_id=task_id,
                    task_name=self.name,
                    queue_name=queue_name,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    safe_payload=safe_payload,
                    attempts=attempts,
                )
            except Exception as dlq_err:
                logger.exception(
                    "Failed in dead-letter failure callback for %s: %s",
                    task_id,
                    dlq_err,
                )
            super().on_failure(exc, task_id, args, kwargs, einfo)

else:
    FashxTask = _DummyTask  # type: ignore[assignment,misc]


app: Any
if Celery is not None:
    broker_use_ssl: dict[str, Any] | None = None
    if settings.redis_url.startswith("rediss://"):
        import ssl

        cert_reqs = (
            ssl.CERT_REQUIRED
            if settings.redis_ssl_cert_reqs == "required"
            else ssl.CERT_NONE
        )
        broker_use_ssl = {"ssl_cert_reqs": cert_reqs}

    app = Celery("fashx", broker=settings.redis_url, backend=None)
    conf_kwargs: dict[str, Any] = {
        "task_serializer": "json",
        "accept_content": ["json"],
        "result_serializer": "json",
        "timezone": "Asia/Kolkata",
        "enable_utc": True,
        "broker_connection_max_retries": 1,
        "broker_connection_retry_on_startup": False,
        "task_ignore_result": True,
        "task_store_errors_even_if_ignored": False,
        "task_acks_late": True,
        "task_reject_on_worker_lost": True,
        "worker_prefetch_multiplier": 1,
        "result_expires": 3600,
        "result_backend_transport_options": {"max_retries": 0},
        "broker_transport_options": {
            "visibility_timeout": 300,
            "max_retries": 3,
            "interval_start": 0,
            "interval_step": 0.2,
            "interval_max": 0.5,
        },
        "task_queues": TASK_QUEUES,
        "task_routes": TASK_ROUTES,
        "task_default_queue": "maintenance",
        "task_default_exchange": "fashx",
        "task_default_routing_key": "maintenance",
        "worker_soft_shutdown_timeout": 90.0,
        "worker_enable_soft_shutdown_on_idle": True,
        "worker_cancel_long_running_tasks_on_connection_loss": True,
        "beat_schedule": {
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
    }
    if broker_use_ssl is not None:
        conf_kwargs["broker_use_ssl"] = broker_use_ssl
    app.conf.update(**conf_kwargs)
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


@app.task(
    name="fashx.workers.app.process_tryon_job",
    bind=True,
    base=FashxTask,
    max_retries=3,
    soft_time_limit=105,
    time_limit=115,
    ignore_result=True,
)
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
    except (ValueError, TypeError) as non_retryable:
        logger.exception(
            "Non-retryable input error in tryon job %s: %s",
            job_id_str,
            non_retryable,
        )
        raise
    except Exception as exc:
        logger.exception("Error executing tryon job %s: %s", job_id_str, exc)
        if self.request.retries < self.max_retries:
            countdown = min(30, 2**self.request.retries)
            raise self.retry(exc=exc, countdown=countdown)
        raise


@app.task(
    name="fashx.workers.app.ingest_catalog_feed",
    bind=True,
    base=FashxTask,
    max_retries=3,
    soft_time_limit=480,
    time_limit=600,
    ignore_result=True,
)
def ingest_catalog_feed(self, source_id: str) -> dict:
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


@app.task(
    name="fashx.workers.app.enrich_garment_task",
    bind=True,
    base=FashxTask,
    max_retries=2,
    soft_time_limit=240,
    time_limit=300,
    ignore_result=True,
)
def enrich_garment_task(self, garment_id: str) -> dict:
    """Execute VLM attribute extraction and embedding for a garment."""
    logger.info("Enriching garment: %s", garment_id)
    garment_uuid = UUID(garment_id)

    from fashx.catalog.application.enrich_garment import (
        EnrichGarmentCommand,
        EnrichGarmentUseCase,
    )
    from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork

    async def _exec() -> dict:
        session_factory = get_session_factory()
        uow = CatalogUnitOfWork(session_factory)
        use_case = EnrichGarmentUseCase(uow)
        result = await use_case.execute(
            EnrichGarmentCommand(garment_id=garment_uuid)
        )
        return {
            "garment_id": str(result.garment_id),
            "status": "enriched",
            "garment_version": result.garment_version,
            "model_version": result.model_version,
        }

    return _run_sync(_exec())


@app.task(
    name="fashx.workers.app.relay_outbox_events",
    bind=True,
    base=FashxTask,
    max_retries=5,
    soft_time_limit=45,
    time_limit=60,
    ignore_result=True,
)
def relay_outbox_events(self) -> dict:
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


@app.task(
    name="fashx.workers.app.sweep_storage_erasure",
    bind=True,
    base=FashxTask,
    max_retries=3,
    soft_time_limit=120,
    time_limit=150,
    ignore_result=True,
)
def sweep_storage_erasure(self) -> dict:
    """Retry any pending S3 media erasure requests via outbox."""
    logger.debug("Executing storage erasure retry sweep")

    from fashx.integration.outbox import run_outbox_worker_once

    async def _exec() -> dict:
        session_factory = get_session_factory()
        storage = get_storage()
        async with session_factory() as session:
            processed = await run_outbox_worker_once(session, storage)
            await session.commit()
            return {
                "status": "erasure_sweep_complete",
                "keys_purged": processed,
            }

    return _run_sync(_exec())


@app.task(
    name="fashx.workers.app.run_retention_jobs",
    bind=True,
    base=FashxTask,
    max_retries=2,
    soft_time_limit=480,
    time_limit=600,
    ignore_result=True,
)
def run_retention_jobs(self) -> dict:
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
