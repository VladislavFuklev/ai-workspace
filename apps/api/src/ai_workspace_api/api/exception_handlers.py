"""The single place a failure becomes an HTTP response.

Two rules the rest of the codebase depends on:

1. **Nothing internal reaches the body.** No stack trace, no SQL, no driver
   message, no file path. The detail goes to the log with the request id; the
   client gets a stable code and a sentence.
2. **Every failure has the same shape**, so a client parses one envelope rather
   than guessing per endpoint. It is the shape
   `apps/web/src/lib/api/errors.ts` already expects.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ai_workspace_api.api.middleware import REQUEST_ID_HEADER
from ai_workspace_api.core.errors import DomainError
from ai_workspace_api.core.logging import get_logger, request_id_var
from ai_workspace_api.schemas.errors import ErrorResponse, FieldError

logger = get_logger(__name__)

# Starlette's own errors, mapped to the project's codes so a 404 from routing
# looks the same to a client as a 404 from a service.
STATUS_CODES = {
    status.HTTP_401_UNAUTHORIZED: "unauthenticated",
    status.HTTP_403_FORBIDDEN: "permission_denied",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_409_CONFLICT: "conflict",
    status.HTTP_413_CONTENT_TOO_LARGE: "payload_too_large",
    status.HTTP_429_TOO_MANY_REQUESTS: "rate_limited",
}


def _request_id(request: Request) -> str | None:
    """Prefers `request.state` over the context variable.

    Starlette's ServerErrorMiddleware runs *outside* RequestContextMiddleware, so
    by the time an unhandled exception reaches a handler the context variable has
    already been reset. The state survives — and that response is exactly where a
    user most needs a reference to quote.
    """
    from_state: str | None = getattr(request.state, "request_id", None)
    return from_state or request_id_var.get()


def _respond(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    detail: list[FieldError] | None = None,
) -> JSONResponse:
    request_id = _request_id(request)
    body = ErrorResponse(code=code, message=message, detail=detail, request_id=request_id)
    response = JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))
    if request_id:
        # The middleware sets this on the way out of a successful request; an
        # error response never reaches that line.
        response.headers[REQUEST_ID_HEADER] = request_id
    return response


async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
    """Anything unhandled.

    The full traceback goes to the log with the request id. The client gets a
    generic sentence and that id — enough to find the log line, and nothing about
    the internals.
    """
    logger.exception("unhandled exception", error_type=type(error).__name__)
    return _respond(
        request,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "internal_error",
        "Something went wrong on our side. Quote the reference if you report this.",
    )


# Handlers are registered against a specific type but typed as taking Exception,
# so each narrows. Not with `assert`: asserts are stripped under `python -O`, and
# a stripped narrowing turns a wrong registration into an AttributeError in
# production.
async def handle_domain_error(request: Request, error: Exception) -> JSONResponse:
    if not isinstance(error, DomainError):
        return await handle_unexpected_error(request, error)

    detail = None
    if isinstance(error.detail, list):
        detail = [FieldError.model_validate(item) for item in error.detail]
    # Expected failures are not exceptional; logging them at error level makes an
    # alert out of a user typing the wrong thing.
    logger.info("domain error", code=error.code, status=error.status_code)
    return _respond(request, error.status_code, error.code, error.message, detail)


async def handle_request_validation_error(request: Request, error: Exception) -> JSONResponse:
    """FastAPI's body and query validation, reshaped into the project's envelope.

    Pydantic's `loc` tuples start with "body" or "query"; the client wants a field
    name it can match against its form.
    """
    if not isinstance(error, RequestValidationError):
        return await handle_unexpected_error(request, error)

    detail = [
        FieldError(
            field=".".join(str(part) for part in item["loc"][1:]) or str(item["loc"][0]),
            message=item["msg"],
        )
        for item in error.errors()
    ]
    return _respond(
        request,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "validation_failed",
        "The request could not be processed. Check the fields listed in detail.",
        detail,
    )


async def handle_http_exception(request: Request, error: Exception) -> JSONResponse:
    if not isinstance(error, StarletteHTTPException):
        return await handle_unexpected_error(request, error)

    code = STATUS_CODES.get(error.status_code, "http_error")
    # Starlette's default detail is a plain status phrase, which is safe. A
    # handler that put a caught exception in there would not be.
    message = error.detail if isinstance(error.detail, str) else "Request failed."
    return _respond(request, error.status_code, code, message)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, handle_domain_error)
    app.add_exception_handler(RequestValidationError, handle_request_validation_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(Exception, handle_unexpected_error)
