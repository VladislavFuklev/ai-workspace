"""Liveness and readiness answer different questions and must fail differently."""

from __future__ import annotations

import pytest

from ai_workspace_api import __version__
from ai_workspace_api.api.app import create_app
from ai_workspace_api.core.settings import Settings

from .conftest import BuildSettings, running_app


async def test_liveness_does_not_touch_any_dependency(settings: Settings) -> None:
    """The whole point: an unreachable database must not fail liveness, or an
    outage restarts every replica in a loop while the database is what is down."""
    app = create_app(settings)  # settings point at a database that does not exist

    async with running_app(app) as client:
        response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive", "version": __version__}


async def test_readiness_is_503_when_the_database_is_unreachable(settings: Settings) -> None:
    app = create_app(settings)

    async with running_app(app) as client:
        response = await client.get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"]["ok"] is False


async def test_readiness_reports_the_failure_type_not_the_message(settings: Settings) -> None:
    """A readiness endpoint is often reachable without authentication, so the
    body carries a class name rather than a connection string in an error."""
    app = create_app(settings)

    async with running_app(app) as client:
        body = (await client.get("/health/ready")).json()

    error = body["checks"]["database"]["error"]
    assert error and " " not in error, error
    assert "password" not in error.lower()
    assert str(settings.database_url.hosts()[0]["host"]) not in error


@pytest.mark.integration
async def test_readiness_is_200_when_everything_is_reachable(
    valid_env: dict[str, str],
    settings_from: BuildSettings,
    database_url: str,
    redis_url: str,
) -> None:
    settings = settings_from({**valid_env, "DATABASE_URL": database_url, "REDIS_URL": redis_url})
    app = create_app(settings)

    async with running_app(app) as client:
        response = await client.get("/health/ready")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"] == {
        "database": {"ok": True, "error": None},
        "redis": {"ok": True, "error": None},
    }


@pytest.mark.integration
async def test_readiness_degrades_when_only_redis_is_down(
    valid_env: dict[str, str], settings_from: BuildSettings, database_url: str
) -> None:
    """Both dependencies are checked, not just the first one that answers."""
    settings = settings_from(
        {**valid_env, "DATABASE_URL": database_url, "REDIS_URL": "redis://127.0.0.1:1/0"}
    )
    app = create_app(settings)

    async with running_app(app) as client:
        response = await client.get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["checks"]["database"]["ok"] is True
    assert body["checks"]["redis"]["ok"] is False


# A dependency that raises before the handler runs currently propagates out of
# the app rather than becoming a response. That is task 2.8's job — the readiness
# handler already catches failures from the query itself, which is the case that
# matters here. The exception-handler test belongs with 2.8.
