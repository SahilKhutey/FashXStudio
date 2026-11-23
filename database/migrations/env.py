from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

import database.models  # noqa: F401
from database.models import Base  # noqa: F401
from fashx.core.settings import get_settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """Filter database objects during autogenerate and alembic check.

    Excludes custom pgvector HNSW vector indexes created via raw SQL
    in migrations 0047 and 0048, and composite primary key unique constraints,
    to prevent false drift detection.
    """
    if type_ == "index" and name in (
        "idx_product_image_embeddings_hnsw",
        "idx_product_text_embeddings_hnsw",
    ):
        return False
    if type_ == "unique_constraint" and name in (
        "uq_theme_definitions_id_version",
        "uq_layout_definitions_id_version",
        "uq_component_definitions_id_version",
    ):
        return False
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(
            lambda sync_conn: context.configure(
                connection=sync_conn,
                target_metadata=target_metadata,
                compare_type=True,
                include_object=include_object,
            )
        )
        async with connection.begin():
            await connection.run_sync(lambda sync_conn: context.run_migrations())
    await connectable.dispose()


def run() -> None:
    import asyncio

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_migrations_online())


run()
