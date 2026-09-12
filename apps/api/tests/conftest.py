"""Shared test fixtures.

Tests must never pick up the developer's real `.env`: a machine with different
values would produce different results. `settings_from` clears every key the
model reads, sets exactly the ones the test asks for, and disables `.env`
discovery — so each test states its whole environment.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from ai_workspace_api.core.settings import Settings

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
MANAGED_KEYS: tuple[str, ...] = (*VALID_ENVIRONMENT, "LOG_LEVEL", "S3_REGION")


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
