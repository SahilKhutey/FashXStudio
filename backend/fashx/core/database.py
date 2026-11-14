from __future__ import annotations

import time
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .metrics import emit_metric
from .settings import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args: dict[str, Any] = {}
        if settings.db_ssl_ca_file:
            import ssl

            connect_args["ssl"] = ssl.create_default_context(
                cafile=settings.db_ssl_ca_file
            )
        kwargs: dict[str, Any] = {
            "pool_pre_ping": True,
            "pool_recycle": 1800,
            "connect_args": connect_args,
        }
        if settings.database_url.startswith("postgresql") or settings.database_url.startswith("postgres"):
            kwargs["pool_size"] = settings.db_pool_size
            kwargs["max_overflow"] = settings.db_max_overflow
            kwargs["pool_timeout"] = settings.db_pool_timeout_s or settings.db_pool_timeout
        _engine = create_async_engine(settings.database_url, **kwargs)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with get_session_factory()() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


def get_db_pool_metrics() -> dict[str, int]:
    """Retrieve current connection pool utilization metrics from the active engine."""
    engine = _engine
    if engine is None or not hasattr(engine, "sync_engine"):
        return {"size": 0, "checked_in": 0, "checked_out": 0, "overflow": 0}

    pool = engine.sync_engine.pool
    if hasattr(pool, "size"):
        return {
            "size": getattr(pool, "size", lambda: 0)(),
            "checked_in": getattr(pool, "checkedin", lambda: 0)(),
            "checked_out": getattr(pool, "checkedout", lambda: 0)(),
            "overflow": getattr(pool, "overflow", lambda: 0)(),
        }
    return {"size": 0, "checked_in": 0, "checked_out": 0, "overflow": 0}


def emit_db_pool_metrics(environment: str = "dev") -> None:
    """Publish connection pool metrics to CloudWatch EMF."""
    pool_data = get_db_pool_metrics()
    emit_metric(
        "DBPoolCheckedOut",
        float(pool_data["checked_out"]),
        unit="Count",
        service="api",
        environment=environment,
        namespace="FashX/Database",
    )
    emit_metric(
        "DBPoolOverflow",
        float(pool_data["overflow"]),
        unit="Count",
        service="api",
        environment=environment,
        namespace="FashX/Database",
    )


async def check_database() -> bool:
    from sqlalchemy import text

    settings = get_settings()
    env = getattr(settings, "env", "dev")
    started = time.perf_counter()

    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        emit_metric(
            "DBQueryLatency",
            latency_ms,
            unit="Milliseconds",
            service="api",
            environment=env,
            dimensions={"Operation": "SELECT_1"},
            namespace="FashX/Database",
        )
        return True
    except Exception:
        emit_metric(
            "DBConnectionErrors",
            1.0,
            unit="Count",
            service="api",
            environment=env,
            dimensions={"Operation": "SELECT_1"},
            namespace="FashX/Database",
        )
        return False
