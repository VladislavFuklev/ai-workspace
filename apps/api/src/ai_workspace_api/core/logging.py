"""Structured logging.

JSON in every environment but local, because a log line is a record something
will query later — and grepping a formatted sentence is how a five-minute
investigation becomes an hour.

Two things every line carries: the request id, so one user's journey can be
followed across services, and the environment. Two things no line carries:
secrets, and the content of documents or prompts. Phase 10 needs counts and
durations; it does not need the text.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any

import structlog

from ai_workspace_api.core.settings import Environment, Settings

# A context variable rather than a parameter threaded through every call: the
# request id must reach a log line written six frames down in a repository.
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Substrings that must never appear as a logged key. Belt and braces — the real
# defence is not passing them, but a redactor turns a mistake into a redaction
# rather than a leak.
SENSITIVE_KEYS = (
    "password",
    "secret",
    "token",
    "authorization",
    "api_key",
    "apikey",
    "cookie",
    "credential",
)
REDACTED = "[redacted]"


def add_request_id(_logger: object, _method: str, event: dict[str, Any]) -> dict[str, Any]:
    request_id = request_id_var.get()
    if request_id is not None:
        event["request_id"] = request_id
    return event


def redact_sensitive(_logger: object, _method: str, event: dict[str, Any]) -> dict[str, Any]:
    """Replaces the value of any key that looks like a credential."""
    for key in list(event):
        if any(marker in key.lower() for marker in SENSITIVE_KEYS):
            event[key] = REDACTED
    return event


def configure_logging(settings: Settings) -> None:
    """Configures structlog and routes the standard library through it.

    Third-party libraries log through `logging`; without this they would write in
    a different format, which defeats the point of structured output.
    """
    shared: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        add_request_id,
        redact_sensitive,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer: Any = (
        structlog.dev.ConsoleRenderer()
        if settings.environment is Environment.LOCAL
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        # The last processor hands the event dict to the stdlib formatter rather
        # than rendering it. Rendering here *and* in the formatter produces a JSON
        # object whose "event" is another JSON object.
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping()[settings.log_level.value]
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Bring the standard library's own records through the same processors.
    handler = logging.StreamHandler()
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=renderer,
            foreign_pre_chain=shared,
        )
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level.value)

    # uvicorn installs its own handlers; let them propagate to ours instead.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger
