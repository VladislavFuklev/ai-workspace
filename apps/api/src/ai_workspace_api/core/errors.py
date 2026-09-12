"""Domain exceptions.

A service raises one of these; the API layer translates it to HTTP exactly once
(`api/exception_handlers.py`). Raising `HTTPException` from inside business logic
would tie the domain to a transport and make the same rule untestable without a
request.
"""

from __future__ import annotations

from typing import Any


class DomainError(Exception):
    """Base for every expected failure.

    `code` is machine-readable and stable — a client branches on it, so changing
    one is a breaking change. `message` is safe to show a user.
    """

    code: str = "internal_error"
    status_code: int = 500

    def __init__(self, message: str, *, detail: Any | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class NotFoundError(DomainError):
    """The resource does not exist — or the caller may not know that it does.

    Tenant isolation uses this deliberately: answering 403 for another
    organisation's document confirms the document exists.
    """

    code = "not_found"
    status_code = 404


class PermissionDeniedError(DomainError):
    """The caller is known, the resource is known to them, and the answer is no."""

    code = "permission_denied"
    status_code = 403


class AuthenticationError(DomainError):
    code = "unauthenticated"
    status_code = 401


class ConflictError(DomainError):
    """The request is valid but the current state refuses it."""

    code = "conflict"
    status_code = 409


class ValidationError(DomainError):
    """Business-rule validation, as opposed to a malformed request body.

    `detail` carries `{field, message}` entries so the client can put each message
    back on its field.
    """

    code = "validation_failed"
    status_code = 422


class RateLimitedError(DomainError):
    code = "rate_limited"
    status_code = 429


class ServiceUnavailableError(DomainError):
    """A dependency the request needed is down. Retrying may work."""

    code = "service_unavailable"
    status_code = 503
