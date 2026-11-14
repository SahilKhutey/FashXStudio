import pytest
from sqlalchemy import text

from fashx.core.database import get_db_pool_metrics, get_session_factory


@pytest.mark.asyncio
async def test_database_ping_select_1():
    session_factory = get_session_factory()
    async with session_factory() as session:
        val = (await session.execute(text("SELECT 1"))).scalar_one()
        assert val == 1


@pytest.mark.asyncio
async def test_database_ephemeral_table_write_and_read():
    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(
            text("""
            CREATE TEMPORARY TABLE test_deploy_val (
                id INTEGER PRIMARY KEY,
                val TEXT NOT NULL
            )
        """)
        )
        await session.execute(
            text("""
            INSERT INTO test_deploy_val (id, val) VALUES (1, 'staging-verified')
        """)
        )
        res = (
            await session.execute(
                text("""
            SELECT val FROM test_deploy_val WHERE id = 1
        """)
            )
        ).scalar_one()
        assert res == "staging-verified"


def test_database_pool_metrics_inspection():
    metrics = get_db_pool_metrics()
    assert "size" in metrics
    assert "checked_in" in metrics
    assert "checked_out" in metrics
    assert metrics["size"] >= 0
