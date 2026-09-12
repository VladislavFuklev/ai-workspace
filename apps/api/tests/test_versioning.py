"""Versioned routes live under the prefix; probes do not."""

from __future__ import annotations

import pytest
from fastapi import APIRouter
from pydantic import ValidationError

from ai_workspace_api.api.app import create_app
from ai_workspace_api.api.v1 import api_router
from ai_workspace_api.core.settings import Settings

from .conftest import BuildSettings, running_app


async def test_health_is_not_versioned(settings: Settings) -> None:
    """A probe URL that changes with the API version breaks every deployment.

    Asserted by request rather than by reading `app.routes`: FastAPI 0.141 keeps
    an included router as a single `_IncludedRouter` entry instead of flattening
    its routes, so introspection there sees nothing.
    """
    async with running_app(create_app(settings)) as client:
        assert (await client.get("/health/live")).status_code == 200
        assert (await client.get("/health/ready")).status_code in (200, 503)
        assert (await client.get(f"{settings.api_prefix}/health/live")).status_code == 404


async def test_a_versioned_route_is_reachable_under_the_prefix(settings: Settings) -> None:
    app = create_app(settings)
    probe = APIRouter()

    @probe.get("/probe")
    async def probe_route() -> dict[str, bool]:
        return {"ok": True}

    app.include_router(probe, prefix=settings.api_prefix)

    async with running_app(app) as client:
        assert (await client.get(f"{settings.api_prefix}/probe")).status_code == 200
        # And not at the bare path — otherwise the prefix is decoration.
        assert (await client.get("/probe")).status_code == 404


async def test_the_prefix_comes_from_settings(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    settings = settings_from({**valid_env, "API_PREFIX": "/api/v2"})
    app = create_app(settings)
    probe = APIRouter()

    @probe.get("/probe")
    async def probe_route() -> dict[str, bool]:
        return {"ok": True}

    app.include_router(probe, prefix=settings.api_prefix)

    async with running_app(app) as client:
        assert (await client.get("/api/v2/probe")).status_code == 200
        assert (await client.get("/api/v1/probe")).status_code == 404


@pytest.mark.parametrize("bad", ["api/v1", "/api/v1/", "/API/v1", "", "/api v1"])
def test_a_malformed_prefix_is_refused(
    valid_env: dict[str, str], settings_from: BuildSettings, bad: str
) -> None:
    """A trailing slash or a missing leading one produces unreachable routes."""
    with pytest.raises(ValidationError):
        settings_from({**valid_env, "API_PREFIX": bad})


def test_the_v1_router_exists_and_is_empty_for_now() -> None:
    """Endpoints arrive with their phases; this asserts the seam, not content."""
    assert api_router.routes == []
