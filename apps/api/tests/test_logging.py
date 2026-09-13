"""Log records: one id per request, JSON off local, and no credentials."""

from __future__ import annotations

import io
import json
import logging
import uuid

import pytest
import structlog

from ai_workspace_api.api.app import create_app
from ai_workspace_api.api.middleware import REQUEST_ID_HEADER
from ai_workspace_api.core.logging import (
    REDACTED,
    configure_logging,
    get_logger,
    redact_sensitive,
    request_id_var,
)
from ai_workspace_api.core.settings import Settings

from .conftest import BuildSettings, production, running_app


def capture(settings: Settings) -> io.StringIO:
    """Configures logging and returns the buffer it writes to.

    The handler captures its stream when it is created, so capsys — which swaps
    sys.stderr afterwards — never sees these lines. Swapping the handler's own
    stream is the reliable way.
    """
    configure_logging(settings)
    buffer = io.StringIO()
    logging.getLogger().handlers[0].setStream(buffer)  # type: ignore[attr-defined]
    return buffer


@pytest.mark.parametrize(
    "key",
    [
        "password",
        "user_password",
        "SECRET",
        "s3_secret_key",
        "authorization",
        "api_key",
        "session_cookie",
        "refresh_token",
        "aws_credential",
    ],
)
def test_credential_shaped_keys_are_redacted(key: str) -> None:
    assert redact_sensitive(None, "info", {key: "hunter2"})[key] == REDACTED


def test_ordinary_keys_survive() -> None:
    event = redact_sensitive(None, "info", {"document_id": "abc", "duration_ms": 12})

    assert event == {"document_id": "abc", "duration_ms": 12}


async def test_every_response_carries_a_request_id(settings: Settings) -> None:
    async with running_app(create_app(settings)) as client:
        response = await client.get("/")

    assert uuid.UUID(response.headers[REQUEST_ID_HEADER])


async def test_two_requests_get_different_ids(settings: Settings) -> None:
    async with running_app(create_app(settings)) as client:
        first = (await client.get("/")).headers[REQUEST_ID_HEADER]
        second = (await client.get("/")).headers[REQUEST_ID_HEADER]

    assert first != second


async def test_a_valid_inbound_id_is_honoured(settings: Settings) -> None:
    """So a trace can span services."""
    supplied = str(uuid.uuid4())

    async with running_app(create_app(settings)) as client:
        response = await client.get("/", headers={REQUEST_ID_HEADER: supplied})

    assert response.headers[REQUEST_ID_HEADER] == supplied


@pytest.mark.parametrize("hostile", ["not-a-uuid", "../../etc/passwd", "a\nb", "' OR 1=1"])
async def test_a_malformed_inbound_id_is_replaced(settings: Settings, hostile: str) -> None:
    """The value is echoed in a header and written to logs; accepting arbitrary
    client input there is log injection."""
    async with running_app(create_app(settings)) as client:
        response = await client.get("/", headers={REQUEST_ID_HEADER: hostile})

    returned = response.headers[REQUEST_ID_HEADER]
    assert returned != hostile
    assert uuid.UUID(returned)


def test_output_is_json_outside_local(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    buffer = capture(settings_from(production(valid_env)))
    get_logger("probe").info("written", document_id="abc", password="hunter2")

    payload = json.loads(buffer.getvalue().strip().splitlines()[-1])

    assert payload["event"] == "written"
    assert payload["document_id"] == "abc"
    assert payload["password"] == REDACTED
    assert payload["level"] == "info"


def test_the_request_id_reaches_a_log_line_written_elsewhere(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    """A repository six frames down must not need the id passed to it."""
    buffer = capture(settings_from(production(valid_env)))
    known = str(uuid.uuid4())
    token = request_id_var.set(known)
    try:
        get_logger("deep").info("from a repository")
    finally:
        request_id_var.reset(token)

    assert json.loads(buffer.getvalue().strip().splitlines()[-1])["request_id"] == known


async def test_the_request_log_line_carries_the_request_id(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    """The success line is written after the request completes; resetting the
    context variable before writing it drops the id silently."""
    # create_app configures logging itself, which replaces the root handler — so
    # the buffer has to be attached after the app exists, not before.
    app = create_app(settings_from(production(valid_env)))
    buffer = io.StringIO()
    logging.getLogger().handlers[0].setStream(buffer)  # type: ignore[attr-defined]

    async with running_app(app) as client:
        returned = (await client.get("/")).headers[REQUEST_ID_HEADER]

    lines = [json.loads(line) for line in buffer.getvalue().strip().splitlines() if line]
    request_lines = [line for line in lines if line.get("event") == "request"]

    assert request_lines, buffer.getvalue()
    assert request_lines[-1]["request_id"] == returned
    assert request_lines[-1]["status"] == 200


def test_local_output_is_human_readable(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    buffer = capture(settings_from({**valid_env, "ENVIRONMENT": "local"}))
    get_logger("probe").info("readable")

    output = buffer.getvalue().strip()

    assert "readable" in output
    with pytest.raises(json.JSONDecodeError):
        json.loads(output.splitlines()[-1])


@pytest.fixture(autouse=True)
def _restore_logging(settings: Settings) -> None:
    """Configuration is global; leave it as the rest of the suite expects."""
    structlog.reset_defaults()
    configure_logging(settings)
