"""Request-scoped middleware."""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ai_workspace_api.core.logging import get_logger, request_id_var

REQUEST_ID_HEADER = "X-Request-ID"
logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Gives every request an id, logs its outcome, and returns the id.

    An inbound id is honoured so a trace can span services, but it is replaced if
    it does not look like a UUID: the value is echoed in a response header and
    written to logs, and accepting arbitrary client input there invites log
    injection.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = _clean(request.headers.get(REQUEST_ID_HEADER))
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        # Every log line below must be written before the context variable is
        # reset, or it goes out without the id — which is the whole point of it.
        try:
            try:
                response = await call_next(request)
            except Exception:
                # Logged here so a failure has the same shape as a success; the
                # response itself is task 2.8's business.
                logger.exception(
                    "request failed",
                    method=request.method,
                    path=request.url.path,
                    duration_ms=_elapsed_ms(started),
                )
                raise
            logger.info(
                "request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=_elapsed_ms(started),
            )
        finally:
            request_id_var.reset(token)

        response.headers[REQUEST_ID_HEADER] = request_id
        return response


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)


def _clean(candidate: str | None) -> str:
    if candidate:
        try:
            return str(uuid.UUID(candidate))
        except ValueError:
            pass
    return str(uuid.uuid4())
