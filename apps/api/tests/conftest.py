"""Shared test fixtures.

Tests must never pick up the developer's real `.env`: a machine with different
values would produce different results. `settings_from` clears every key the
model reads, sets exactly the ones the test asks for, and disables `.env`
discovery — so each test states its whole environment.
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator, Callable

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from ai_workspace_api.core.settings import Settings
from ai_workspace_api.models import NAMING_CONVENTION

BuildSettings = Callable[[dict[str, str]], Settings]

VALID_ENVIRONMENT: dict[str, str] = {
    "ENVIRONMENT": "test",
    "DATABASE_URL": "postgresql+psycopg://user:pw@localhost:5433/ai_workspace",
    "REDIS_URL": "redis://localhost:6380/0",
    "S3_ENDPOINT_URL": "http://localhost:9000",
    "S3_BUCKET": "ai-workspace-documents",
    "S3_ACCESS_KEY": "test-access-key",
    "S3_SECRET_KEY": "test-secret-key",
}

# Every variable Settings looks at, so a leftover one cannot influence a test.
MANAGED_KEYS: tuple[str, ...] = (
    *VALID_ENVIRONMENT,
    "LOG_LEVEL",
    "S3_REGION",
    "CORS_ORIGINS",
    "SERVICE_NAME",
    "API_PREFIX",
    "MAX_REQUEST_BODY_BYTES",
)


@pytest.fixture
def valid_env() -> dict[str, str]:
    """A complete, valid environment. Copy and mutate it per test."""
    return dict(VALID_ENVIRONMENT)


@pytest.fixture
def settings_from(monkeypatch: pytest.MonkeyPatch) -> BuildSettings:
    """Build Settings from a given environment, the way production does."""

    def build(env: dict[str, str]) -> Settings:
        for key in MANAGED_KEYS:
            monkeypatch.delenv(key, raising=False)
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        # _env_file=None isolates the test from the repository's own .env. It is a
        # documented pydantic-settings init argument that the type stubs omit.
        return Settings(_env_file=None)  # type: ignore[call-arg]

    return build


@pytest.fixture
def settings(valid_env: dict[str, str], settings_from: BuildSettings) -> Settings:
    """A complete Settings object for tests that need one rather than build one."""
    return settings_from(valid_env)


@pytest.fixture(scope="session")
def redis_url() -> str:
    """The real Redis, from the same environment the developer already has.

    A hard-coded fallback here would make the test pass locally and assert a
    degraded service in CI — which is exactly what it did before.
    """
    import os

    url = os.environ.get("REDIS_URL")
    if not url:
        pytest.skip("REDIS_URL is not set; run scripts/dev-up.sh and copy .env")
    return url


@pytest.fixture(scope="session")
def database_url() -> str:
    """The real database, from the environment the developer already has.

    Integration tests use the compose stack rather than a substitute: SQLite is a
    different database, and a query using pgvector or a Postgres-specific
    constraint proves nothing there.
    """
    import os

    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL is not set; run scripts/dev-up.sh and copy .env")
    return url


class ScratchBase(DeclarativeBase):
    """Declarative base for throwaway tables in tests.

    Not named Test* — pytest tries to collect any class with that prefix.

    Separate metadata from the application's: a scratch table registered on
    `Base.metadata` would make the model/schema drift check report a difference
    that does not exist.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


@contextlib.asynccontextmanager
async def running_app(
    app: FastAPI, *, raise_app_exceptions: bool = True
) -> AsyncIterator[httpx.AsyncClient]:
    """A client talking to an app whose lifespan has actually run.

    `httpx.ASGITransport` does **not** run the lifespan — it dispatches requests
    only. Anything the lifespan puts on `app.state`, such as the session factory,
    is therefore missing unless the lifespan is entered explicitly.

    `raise_app_exceptions` stays on by default so an unexpected failure in a test
    is loud. Pass False to see what a real client sees: Starlette builds the 500
    response and then re-raises so the server can log it, and only a transport
    that swallows the re-raise shows the response body.
    """
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=raise_app_exceptions),
            base_url="http://test",
        ) as client,
    ):
        yield client
