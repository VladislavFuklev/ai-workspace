"""The application assembles, answers, and uses the settings it was given."""

from __future__ import annotations

import httpx
import pytest

from ai_workspace_api import __version__
from ai_workspace_api.api.app import create_app
from ai_workspace_api.core.settings import Environment, Settings

from .conftest import BuildSettings


@pytest.fixture
def client(settings: Settings) -> httpx.AsyncClient:
    """Talks to the app in-process: no port, no network, no ordering surprises."""
    app = create_app(settings)
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_root_identifies_the_service(client: httpx.AsyncClient, settings: Settings) -> None:
    async with client:
        response = await client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "ai-workspace-api",
        "version": __version__,
        "environment": settings.environment.value,
    }


async def test_uses_the_injected_settings_not_the_environment(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    """The factory must not reach for the module-level singleton."""
    app = create_app(settings_from({**valid_env, "ENVIRONMENT": "production"}))

    assert app.state.settings.environment is Environment.PRODUCTION

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.json()["environment"] == "production"


async def test_docs_are_closed_outside_local(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    """Interactive docs are a development affordance; 2.10 decides production."""
    local = create_app(settings_from({**valid_env, "ENVIRONMENT": "local"}))
    production = create_app(settings_from({**valid_env, "ENVIRONMENT": "production"}))

    assert local.docs_url == "/docs"
    assert production.docs_url is None
    assert production.openapi_url is None


async def test_lifespan_runs(settings: Settings) -> None:
    """A failure in startup must surface as a failure to start, not a stuck app."""
    app = create_app(settings)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # ASGITransport runs the lifespan; a raising lifespan fails this call.
        assert (await client.get("/")).status_code == 200
