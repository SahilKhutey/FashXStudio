from collections.abc import Iterator
from typing import Any
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from fashx.core.settings import get_settings

_sync_engine = None
_SyncSessionLocal: sessionmaker[Session] | None = None


def get_sync_engine() -> Any:
    global _sync_engine
    if _sync_engine is None:
        settings = get_settings()
        # Convert asyncpg/aiosqlite to sync driver for sync workers/scripts
        sync_url = (
            settings.database_url.replace("+asyncpg", "")
            .replace("+aiosqlite", "")
        )
        _sync_engine = create_engine(sync_url, pool_pre_ping=True, pool_recycle=1800)
    return _sync_engine


def get_sync_session_factory() -> sessionmaker[Session]:
    global _SyncSessionLocal
    if _SyncSessionLocal is None:
        _SyncSessionLocal = sessionmaker(
            bind=get_sync_engine(),
            expire_on_commit=False,
            future=True,
        )
    return _SyncSessionLocal


def get_db() -> Iterator[Session]:
    """Yield a synchronous SQLAlchemy session with automatic rollback on error."""
    factory = get_sync_session_factory()
    db = factory()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


class SqlUnitOfWork:
    """Synchronous Unit of Work for background workers, tasks, and scripts."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def __enter__(self) -> "SqlUnitOfWork":
        return self

    def __exit__(self, exc_type: Any, *_: Any) -> None:
        if exc_type is not None:
            self.db.rollback()
        else:
            self.db.commit()
