"""The configuration contract: a valid environment loads, an incomplete or
malformed one stops the process with a message naming the offending field."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from pydantic import ValidationError

from ai_workspace_api.core.settings import Environment, LogLevel, Settings, get_settings

BuildSettings = Callable[[dict[str, str]], Settings]


def test_valid_environment_loads(valid_env: dict[str, str], settings_from: BuildSettings) -> None:
    settings = settings_from(valid_env)

    assert settings.environment is Environment.TEST
    assert settings.log_level is LogLevel.INFO  # default
    assert settings.s3_bucket == "ai-workspace-documents"
    assert settings.s3_region == "us-east-1"  # default
    # PostgresDsn is a MultiHostUrl: the connection details live in .hosts().
    (host,) = settings.database_url.hosts()
    assert host["host"] == "localhost"
    assert host["port"] == 5433


@pytest.mark.parametrize(
    "missing",
    ["DATABASE_URL", "REDIS_URL", "S3_ENDPOINT_URL", "S3_BUCKET", "S3_ACCESS_KEY", "S3_SECRET_KEY"],
)
def test_missing_required_value_names_the_field(
    valid_env: dict[str, str], settings_from: BuildSettings, missing: str
) -> None:
    del valid_env[missing]

    with pytest.raises(ValidationError) as caught:
        settings_from(valid_env)

    report = str(caught.value)
    assert missing.lower() in report.lower(), report
    assert "Field required" in report, report


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("DATABASE_URL", "not-a-url"),
        ("DATABASE_URL", "mysql://user:pw@localhost/db"),  # wrong scheme
        ("REDIS_URL", "http://localhost:6380"),
        ("S3_ENDPOINT_URL", "localhost:9000"),  # no scheme
        ("S3_BUCKET", "ab"),  # shorter than the 3-character minimum
        ("ENVIRONMENT", "prodution"),  # typo in an enum member
        ("LOG_LEVEL", "verbose"),
    ],
)
def test_malformed_value_names_the_field(
    valid_env: dict[str, str], settings_from: BuildSettings, field: str, value: str
) -> None:
    valid_env[field] = value

    with pytest.raises(ValidationError) as caught:
        settings_from(valid_env)

    assert field.lower() in str(caught.value).lower(), str(caught.value)


def test_secrets_are_not_exposed_by_repr(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    """A settings object reaches logs and tracebacks; the secrets must not."""
    settings = settings_from(valid_env)

    rendered = f"{settings!r} {settings.s3_secret_key}"

    assert "test-secret-key" not in rendered
    assert settings.s3_secret_key.get_secret_value() == "test-secret-key"


def test_environment_predicates(valid_env: dict[str, str], settings_from: BuildSettings) -> None:
    assert settings_from({**valid_env, "ENVIRONMENT": "production"}).is_production is True
    assert settings_from({**valid_env, "ENVIRONMENT": "production"}).debug is False
    assert settings_from({**valid_env, "ENVIRONMENT": "local"}).debug is True


def test_unmodelled_keys_are_ignored(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    """The .env is shared with Docker Compose, which needs keys the API does not."""
    settings = settings_from({**valid_env, "POSTGRES_PORT": "5433", "MINIO_CONSOLE_PORT": "9001"})

    assert settings.s3_bucket == "ai-workspace-documents"


def test_get_settings_is_cached(
    valid_env: dict[str, str], settings_from: BuildSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings_from(valid_env)  # puts the valid environment in place
    monkeypatch.chdir("/")  # no .env to discover from the filesystem root
    get_settings.cache_clear()
    try:
        assert get_settings() is get_settings()
    finally:
        get_settings.cache_clear()
