import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


def validate_application_sql_operation(sql: str) -> None:
    """Validate that application runtime queries never attempt prohibited DDL operations."""
    prohibited_keywords = ["DROP TABLE", "CREATE TABLE", "ALTER TABLE", "TRUNCATE", "DROP DATABASE"]
    normalized = " ".join(sql.upper().split())
    for kw in prohibited_keywords:
        if kw in normalized:
            raise PermissionError(f"Prohibited DDL operation detected for application role: {kw}")


def test_allowed_dml_queries_pass_permission_check():
    allowed = [
        "SELECT * FROM user_style_profiles WHERE id = 'test-id'",
        "INSERT INTO garments (id, brand, title) VALUES ('g1', 'Zara', 'Shirt')",
        "UPDATE tryon_jobs SET status = 'completed' WHERE id = 'j1'",
        "DELETE FROM shopper_favorites WHERE user_id = 'u1' AND garment_id = 'g1'",
    ]
    for q in allowed:
        validate_application_sql_operation(q)


def test_prohibited_ddl_queries_raise_permission_error():
    prohibited = [
        "DROP TABLE users",
        "CREATE TABLE test (id INT)",
        "ALTER TABLE garments DROP COLUMN title",
        "TRUNCATE TABLE catalog_products",
        "DROP DATABASE fashx_prod",
    ]
    for q in prohibited:
        with pytest.raises(PermissionError, match="Prohibited DDL operation"):
            validate_application_sql_operation(q)


@pytest.mark.asyncio
async def test_runtime_engine_executes_dml():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.execute(text("CREATE TABLE temp_test (id INT, val TEXT)"))
        await conn.execute(text("INSERT INTO temp_test (id, val) VALUES (1, 'hello')"))
        result = await conn.execute(text("SELECT val FROM temp_test WHERE id = 1"))
        row = result.scalar_one_or_none()
        assert row == "hello"
    await engine.dispose()
