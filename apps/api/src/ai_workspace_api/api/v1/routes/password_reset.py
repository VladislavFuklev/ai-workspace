"""Password reset endpoints.

Neither endpoint reveals whether an address has an account. The request endpoint
answers identically; the confirm endpoint gives one message for an unknown,
expired, used or foreign token.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from ai_workspace_api.api.cookies import clear_session_cookies
from ai_workspace_api.api.dependencies import SessionDep, SettingsDep
from ai_workspace_api.schemas.auth import (
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetResponse,
)
from ai_workspace_api.services.password_reset import PasswordResetService

router = APIRouter(prefix="/auth/password-reset", tags=["auth"])


@router.post(
    "/request",
    name="request_password_reset",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=PasswordResetResponse,
    summary="Ask for a reset link",
    description=(
        "Answers identically whether or not the address has an account.\n\n"
        "**Delivery is not built yet.** The token is created but nothing sends "
        "it, so the flow cannot be completed by a user until email exists. There "
        "is deliberately no development mode that returns the token — that is "
        "the kind of convenience that reaches production."
    ),
)
async def request_reset(
    payload: PasswordResetRequest, session: SessionDep, settings: SettingsDep
) -> PasswordResetResponse:
    await PasswordResetService(session, settings).request(payload.email)
    # The token is deliberately dropped: sending it is the missing half, and
    # returning it here would make the endpoint an account-takeover API.
    return PasswordResetResponse()


@router.post(
    "/confirm",
    name="confirm_password_reset",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Set a new password with a reset token",
    description=(
        "On success every session for the account is revoked. A reset is what "
        "someone does when they believe they have been compromised, so leaving "
        "the intruder signed in would defeat it."
    ),
)
async def confirm_reset(
    payload: PasswordResetConfirm,
    response: Response,
    session: SessionDep,
    settings: SettingsDep,
) -> None:
    await PasswordResetService(session, settings).confirm(payload.token, payload.password)
    # This browser's cookies are stale too — the sessions they refer to are gone.
    clear_session_cookies(response, settings)
