"""Alembic environment.

The URL comes from the application's settings rather than `alembic.ini`, so a
migration can never run against a different database than the app — the classic
way a schema and a deployment drift apart.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from ai_workspace_api.core.settings import get_settings

# Importing the package registers every model on Base.metadata. A model that is
# not imported here is invisible to autogenerate, which will then write a
# migration that drops its table.
from ai_workspace_api.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", str(get_settings().database_url))

target_metadata = Base.metadata


def _configure(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Without these, autogenerate misses a column changing type or becoming
        # nullable — it would silently produce an empty migration.
        compare_type=True,
        compare_server_default=True,
        # Names come from the metadata convention (task 2.4) rather than Postgres.
        render_as_batch=False,
    )


def run_migrations_offline() -> None:
    """Emit SQL without a database, for a review or a DBA-applied change."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _run(connection: Connection) -> None:
    _configure(connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with engine.connect() as connection:
        await connection.run_sync(_run)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
