import tempfile

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from fashx.core.settings import Settings


@pytest.mark.asyncio
async def test_committed_data_persists_across_distinct_sessions():
    with tempfile.NamedTemporaryFile(suffix=".db") as tf:
        db_path = tf.name

    db_url = f"sqlite+aiosqlite:///{db_path}"
    engine1 = create_async_engine(db_url)
    session_factory1 = async_sessionmaker(engine1, expire_on_commit=False)

    async with engine1.begin() as conn:
        await conn.execute(text("CREATE TABLE test_items (id TEXT PRIMARY KEY, name TEXT)"))

    async with session_factory1() as session:
        await session.execute(text("INSERT INTO test_items (id, name) VALUES ('item-1', 'Denim Jacket')"))
        await session.commit()

    await engine1.dispose()

    # Re-open independent engine to verify persistence across restarts
    engine2 = create_async_engine(db_url)
    session_factory2 = async_sessionmaker(engine2, expire_on_commit=False)

    async with session_factory2() as session:
        result = await session.execute(text("SELECT name FROM test_items WHERE id = 'item-1'"))
        val = result.scalar_one_or_none()
        assert val == "Denim Jacket"

    await engine2.dispose()


@pytest.mark.asyncio
async def test_uncommitted_transaction_rolls_back():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.execute(text("CREATE TABLE test_rollback (id INT PRIMARY KEY, val TEXT)"))

    async with session_factory() as session:
        await session.execute(text("INSERT INTO test_rollback (id, val) VALUES (1, 'initial')"))
        await session.commit()

    # Attempt failed transaction
    try:
        async with session_factory() as session:
            await session.execute(text("INSERT INTO test_rollback (id, val) VALUES (2, 'uncommitted')"))
            raise RuntimeError("Forced simulation error")
    except RuntimeError:
        pass

    async with session_factory() as session:
        res = await session.execute(text("SELECT COUNT(*) FROM test_rollback"))
        count = res.scalar_one()
        assert count == 1

    await engine.dispose()


def test_repo_backend_setting_configuration():
    local_dev = Settings(REPO_BACKEND="sql", ENV="dev", APP_ENV="development")
    assert local_dev.repo_backend == "sql"

    with pytest.raises(Exception, match="staging requires REPO_BACKEND=sql"):
        Settings(
            REPO_BACKEND="memory",
            ENV="staging",
            APP_ENV="staging",
            STORAGE_BACKEND="s3",
            S3_BUCKET="bucket",
            AUTH_MODE="jwks",
            AUTH_JWKS_URL="https://auth.example.com",
            CORS_ORIGINS=["https://staging.example.com"],
        )
