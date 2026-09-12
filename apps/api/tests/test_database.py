"""Engine and session behaviour against the real database."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ai_workspace_api.core.database import create_engine, create_session_factory, session_scope
from ai_workspace_api.core.settings import Settings

from .conftest import BuildSettings

pytestmark = pytest.mark.integration


@pytest.fixture
async def settings_for_db(
    valid_env: dict[str, str], settings_from: BuildSettings, database_url: str
) -> Settings:
    return settings_from({**valid_env, "DATABASE_URL": database_url})


async def test_engine_connects_and_the_extension_is_present(settings_for_db: Settings) -> None:
    engine = create_engine(settings_for_db)
    try:
        async with engine.connect() as connection:
            assert (await connection.scalar(text("SELECT 1"))) == 1
            # pgvector is what the whole retrieval phase depends on; if it is
            # missing, that should fail here rather than in phase 6.
            version = await connection.scalar(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            )
            assert version is not None, "the vector extension is not installed"
    finally:
        await engine.dispose()


async def test_session_scope_closes_the_session(settings_for_db: Settings) -> None:
    engine = create_engine(settings_for_db)
    factory = create_session_factory(engine)
    try:
        opened = None
        async for session in session_scope(factory):
            opened = session
            assert (await session.scalar(text("SELECT 1"))) == 1
        assert opened is not None
        # A closed session has released its connection back to the pool.
        assert not opened.is_active or opened.get_transaction() is None
    finally:
        await engine.dispose()


async def test_session_scope_rolls_back_on_failure(settings_for_db: Settings) -> None:
    """A handler that raises must not leave a half-applied write behind."""
    engine = create_engine(settings_for_db)
    factory = create_session_factory(engine)
    # Literal statements, not interpolated: S608 forbids building SQL from
    # strings, and that rule is worth keeping switched on for tests too.
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text("CREATE TABLE IF NOT EXISTS rollback_probe (id int primary key)")
            )

        with pytest.raises(RuntimeError):
            async for session in session_scope(factory):
                await session.execute(text("INSERT INTO rollback_probe VALUES (1)"))
                raise RuntimeError("handler failed after writing")

        async with engine.connect() as connection:
            remaining = await connection.scalar(text("SELECT count(*) FROM rollback_probe"))
        assert remaining == 0, "the write survived a failed request"
    finally:
        async with engine.begin() as connection:
            await connection.execute(text("DROP TABLE IF EXISTS rollback_probe"))
        await engine.dispose()


async def test_a_bad_url_fails_at_connect_not_at_import(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    """Creating an engine is lazy; the failure must still be a database error."""
    settings = settings_from(
        {**valid_env, "DATABASE_URL": "postgresql+psycopg://nobody:nope@127.0.0.1:1/none"}
    )
    engine = create_engine(settings)
    try:
        with pytest.raises(SQLAlchemyError):
            async with engine.connect() as connection:
                await connection.scalar(text("SELECT 1"))
    finally:
        await engine.dispose()
