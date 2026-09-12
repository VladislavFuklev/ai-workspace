"""Configuration added in 2.2: origins, service identity, and the production guard."""

from __future__ import annotations

import httpx
import pytest
from pydantic import ValidationError

from ai_workspace_api.api.app import create_app
from ai_workspace_api.core.settings import Settings

from .conftest import BuildSettings


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("http://a.test,http://b.test", ["http://a.test", "http://b.test"]),
        ("http://a.test, http://b.test ,", ["http://a.test", "http://b.test"]),
        ("", []),
        ("   ", []),
    ],
)
def test_origins_parse_from_a_comma_separated_string(
    valid_env: dict[str, str], settings_from: BuildSettings, raw: str, expected: list[str]
) -> None:
    assert settings_from({**valid_env, "CORS_ORIGINS": raw}).cors_origins == expected


def test_wildcard_origin_is_refused_in_production(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    with pytest.raises(ValidationError) as caught:
        settings_from({**valid_env, "ENVIRONMENT": "production", "CORS_ORIGINS": "*"})

    assert "cors_origins" in str(caught.value)


def test_wildcard_origin_is_allowed_outside_production(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    assert settings_from(
        {**valid_env, "ENVIRONMENT": "local", "CORS_ORIGINS": "*"}
    ).cors_origins == ["*"]


async def test_a_permitted_origin_is_allowed(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    app = create_app(settings_from({**valid_env, "CORS_ORIGINS": "http://allowed.test"}))

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/", headers={"Origin": "http://allowed.test"})

    assert response.headers["access-control-allow-origin"] == "http://allowed.test"
    assert response.headers["access-control-allow-credentials"] == "true"


async def test_a_foreign_origin_is_not_allowed(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    app = create_app(settings_from({**valid_env, "CORS_ORIGINS": "http://allowed.test"}))

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/", headers={"Origin": "http://evil.test"})

    assert "access-control-allow-origin" not in response.headers


async def test_no_cors_headers_when_no_origins_are_configured(settings: Settings) -> None:
    """The middleware is not installed at all rather than installed permissively."""
    app = create_app(settings)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/", headers={"Origin": "http://anything.test"})

    assert "access-control-allow-origin" not in response.headers


async def test_service_name_comes_from_settings(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    app = create_app(settings_from({**valid_env, "SERVICE_NAME": "renamed-api"}))

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        assert (await client.get("/")).json()["service"] == "renamed-api"
