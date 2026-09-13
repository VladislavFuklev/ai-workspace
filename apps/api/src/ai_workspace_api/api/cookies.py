"""Session cookies.

One place that decides the flags, because getting one wrong on one endpoint is
how a session leaks.

- `HttpOnly` — script cannot read it, so an XSS bug does not become a stolen
  session.
- `SameSite=Lax` — not sent on a cross-site POST, which is CSRF protection for
  the state-changing endpoints. `Strict` would sign the user out whenever they
  arrive from an external link.
- `Secure` — from settings, forced on in production (task 3.5 guard).
- The refresh cookie's `Path` is the refresh endpoint, so it is not attached to
  every request. A cookie that is never sent cannot be stolen in transit.
"""

from __future__ import annotations

from fastapi import Response

from ai_workspace_api.core.settings import Settings

ACCESS_COOKIE = "ai_workspace_access"
REFRESH_COOKIE = "ai_workspace_refresh"


def refresh_cookie_path(settings: Settings) -> str:
    return f"{settings.api_prefix}/auth/refresh"


def set_session_cookies(
    response: Response, *, access_token: str, refresh_token: str, settings: Settings
) -> None:
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        max_age=settings.access_token_ttl_seconds,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path=refresh_cookie_path(settings),
    )


def clear_session_cookies(response: Response, settings: Settings) -> None:
    """Paths must match the ones used to set them, or the cookies survive."""
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path=refresh_cookie_path(settings))
