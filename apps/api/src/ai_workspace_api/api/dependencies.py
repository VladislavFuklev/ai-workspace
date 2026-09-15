"""Shared FastAPI dependencies.

Everything a handler needs arrives through these, so a test overrides one
dependency instead of patching a module.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ai_workspace_api.core.database import session_scope
from ai_workspace_api.core.settings import Settings
from ai_workspace_api.core.storage import Storage


def get_app_settings(request: Request) -> Settings:
    """The settings the app was built with — not the module-level singleton."""
    settings: Settings = request.app.state.settings
    return settings


SettingsDep = Annotated[Settings, Depends(get_app_settings)]


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """One session per request, closed by the framework when the request ends."""
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async for session in session_scope(factory):
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_storage(request: Request) -> Storage:
    """The store opened at startup.

    A dependency rather than an import, so a test swaps in `InMemoryStorage`
    without a network, and without patching a module that something else may
    have already imported.
    """
    storage: Storage = request.app.state.storage
    return storage


StorageDep = Annotated[Storage, Depends(get_storage)]
