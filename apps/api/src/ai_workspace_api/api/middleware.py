"""Request-scoped middleware."""

from __future__ import annotations

import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ai_workspace_api.core.logging import get_logger, request_id_var

REQUEST_ID_HEADER = "X-Request-ID"
logger = get_logger(__name__)


class RequestContextMiddleware:
    """Gives every request an id, logs its outcome, and returns the id.

    Written as pure ASGI rather than `BaseHTTPMiddleware`. That base class runs
    the downstream app in a task group and re-raises through it, which changes how
    exceptions surface — the reason an unhandled error behaved differently under
    test than against a real server. It also buffers streaming responses, which
    matters from phase 7 onwards when answers stream token by token.

    An inbound id is honoured so a trace can span services, but it is replaced if
    it does not look like a UUID: the value is echoed in a response header and
    written to logs, and accepting arbitrary client input there invites log
    injection.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {key.decode("latin-1").lower(): value for key, value in scope["headers"]}
        raw_id = headers.get(REQUEST_ID_HEADER.lower())
        request_id = _clean(raw_id.decode("latin-1") if raw_id else None)

        # Also on the ASGI state: Starlette's ServerErrorMiddleware sits outside
        # this one, so by the time it handles an unhandled exception the context
        # variable is already reset. That response is exactly where a user most
        # needs a reference to quote.
        scope.setdefault("state", {})["request_id"] = request_id

        token = request_id_var.set(request_id)
        started = time.perf_counter()
        status_code = 500

        async def send_with_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        except Exception:
            # Logged here so a failure has the same shape as a success; turning it
            # into a response is the exception handlers' business.
            logger.exception(
                "request failed",
                method=scope["method"],
                path=scope["path"],
                duration_ms=_elapsed_ms(started),
            )
            raise
        else:
            logger.info(
                "request",
                method=scope["method"],
                path=scope["path"],
                status=status_code,
                duration_ms=_elapsed_ms(started),
            )
        finally:
            request_id_var.reset(token)


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)


def _clean(candidate: str | None) -> str:
    if candidate:
        try:
            return str(uuid.UUID(candidate))
        except ValueError:
            pass
    return str(uuid.uuid4())
