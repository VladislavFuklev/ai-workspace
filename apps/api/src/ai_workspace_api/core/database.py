"""Database engine and session lifecycle.

One engine per process, created at startup and disposed at shutdown; one session
per request, opened and closed by a dependency. Both halves matter: an engine per
request exhausts the server's connection slots, and a session that outlives a
request leaks whatever transaction it was holding.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ai_workspace_api.core.settings import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """The process-wide engine.

    `pool_pre_ping` costs one round trip per checkout and saves the class of
    failure where a connection was closed by the database, a proxy or a laptop
    sleeping, and the first query after that dies rather than reconnecting.
    """
    return create_async_engine(
        str(settings.database_url),
        echo=False,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        # Recycle below the typical proxy idle timeout, for the same reason.
        pool_recycle=1800,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        # Attributes stay readable after commit. Without this, serialising a
        # response after committing triggers a lazy refresh on a closed session.
        expire_on_commit=False,
        autoflush=False,
    )


async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """One unit of work.

    The session is closed whatever happens, and rolled back on the way out if the
    caller left a transaction open — a handler that raises must not leave a
    half-applied write for the next user of that connection.

    Committing is the service layer's job, not this function's: only the caller
    knows where the unit of work ends.
    """
    session = factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
