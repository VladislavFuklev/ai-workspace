"""Typed application configuration.

This module is the only place in the API that reads the environment. Everything
else receives a ``Settings`` instance, so configuration is explicit in signatures
and substitutable in tests.

Validation happens when the object is constructed, so a misconfigured deployment
fails at startup with a message naming the field rather than at the first request
that happens to touch it.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import (
    AnyHttpUrl,
    Field,
    PostgresDsn,
    RedisDsn,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _find_env_file() -> Path | None:
    """Locate the repository's .env by walking up from the working directory.

    The API is run both from the repository root and from ``apps/api``
    (``scripts/dev-api.sh`` does the latter), while ``.env`` lives at the root and
    is shared with Docker Compose. A plain relative filename would resolve against
    whichever directory happened to be current.

    Returns None when there is no file — in a container the values come from the
    environment directly, and that is not an error.
    """
    for directory in (Path.cwd(), *Path.cwd().parents):
        candidate = directory / ".env"
        if candidate.is_file():
            return candidate
        if (directory / ".git").exists():  # stop at the repository root
            break
    return None


class Environment(StrEnum):
    """Deployment environment. Behaviour that differs between environments keys
    off this rather than off a scattered collection of boolean flags."""

    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Settings(BaseSettings):
    """Everything the API reads from the environment.

    No secret has a working default: a missing one must stop the process rather
    than let it run in an insecure but apparently healthy state.
    """

    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        # The repository's .env is shared with Docker Compose and carries keys this
        # object does not model (POSTGRES_PORT, MINIO_CONSOLE_PORT, ...). Ignoring
        # them keeps one .env for the whole project.
        extra="ignore",
        case_sensitive=False,
        # Secrets are only ever revealed by an explicit .get_secret_value().
        validate_default=True,
    )

    environment: Environment = Environment.LOCAL
    log_level: LogLevel = LogLevel.INFO

    service_name: str = "ai-workspace-api"
    api_prefix: str = "/api/v1"

    # NoDecode is required: without it the env source tries to JSON-decode any
    # list field before validators run, so "a,b" fails before it can be split.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=list,
        description="Origins allowed to call the API with credentials.",
    )

    # Documents are uploaded through this API; an unbounded body is a denial of
    # service. Enforced at the edge in task 5.3.
    max_request_body_bytes: Annotated[int, Field(gt=0)] = 25 * 1024 * 1024

    database_url: Annotated[
        PostgresDsn,
        Field(description="SQLAlchemy-style DSN, e.g. postgresql+psycopg://user:pw@host:5432/db"),
    ]
    redis_url: RedisDsn

    # Pool sizing is per process. The ceiling that matters is Postgres's
    # max_connections divided by the number of API processes.
    database_pool_size: Annotated[int, Field(ge=1, le=50)] = 5
    database_max_overflow: Annotated[int, Field(ge=0, le=50)] = 5

    s3_endpoint_url: AnyHttpUrl
    s3_bucket: Annotated[str, Field(min_length=3, max_length=63)]
    s3_access_key: SecretStr
    s3_secret_key: SecretStr
    s3_region: str = "us-east-1"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Accepts a comma-separated string and drops empty entries.

        A trailing comma or a blank `CORS_ORIGINS=` is the most common way this
        setting is written, and an empty origin would silently match nothing.
        """
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def _reject_unsafe_cors_in_production(self) -> Settings:
        """A wildcard origin cannot be combined with credentials.

        Browsers refuse the combination outright, so a deployment configured this
        way fails at the first cross-origin request with a message that points at
        the browser rather than at the configuration. Better to refuse to start.
        """
        if self.environment is Environment.PRODUCTION and "*" in self.cors_origins:
            raise ValueError(
                "cors_origins must not contain '*' in production: the API sends "
                "credentials, and browsers reject a wildcard origin with them."
            )
        return self

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION

    @property
    def debug(self) -> bool:
        return self.environment is Environment.LOCAL


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """The process-wide settings instance.

    Cached so the environment is read and validated once. Tests that need a
    different environment should construct ``Settings(...)`` directly, or call
    ``get_settings.cache_clear()`` after changing the environment.
    """
    return Settings()  # type: ignore[call-arg]  # values come from the environment
