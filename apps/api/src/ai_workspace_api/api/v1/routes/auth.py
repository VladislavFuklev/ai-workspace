"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Cookie, Response, status

from ai_workspace_api.api.cookies import REFRESH_COOKIE, set_session_cookies
from ai_workspace_api.api.dependencies import SessionDep, SettingsDep
from ai_workspace_api.core.errors import AuthenticationError
from ai_workspace_api.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    UserProfile,
)
from ai_workspace_api.services.auth import AuthService
from ai_workspace_api.services.session import SessionService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    name="register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisterResponse,
    summary="Create an account",
    description=(
        "Answers identically whether or not the address was already registered. "
        "A response therefore cannot be used to discover which addresses have "
        "accounts."
    ),
)
async def register(payload: RegisterRequest, session: SessionDep) -> RegisterResponse:
    await AuthService(session).register(
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
    )
    # The return value is deliberately ignored: branching on it here is exactly
    # the enumeration leak this endpoint exists to avoid.
    return RegisterResponse()


@router.post(
    "/login",
    name="login",
    response_model=UserProfile,
    summary="Sign in",
    description=(
        "Sets the session cookies and returns the signed-in user. Every failure "
        "— wrong address, wrong password, disabled account — answers identically."
    ),
)
async def login(
    payload: LoginRequest,
    response: Response,
    session: SessionDep,
    settings: SettingsDep,
) -> UserProfile:
    user = await AuthService(session).authenticate(payload.email, payload.password)
    pair = await SessionService(session, settings).issue(user)
    await session.commit()
    set_session_cookies(
        response,
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        settings=settings,
    )
    return UserProfile.model_validate(user)


@router.post(
    "/refresh",
    name="refresh",
    response_model=UserProfile,
    summary="Exchange the refresh token for a new session",
    description=(
        "Rotates the session: the old refresh token stops working and a new pair "
        "is issued. Presenting a token that was already rotated away revokes "
        "every session from the same sign-in — that is a stolen token being "
        "replayed."
    ),
)
async def refresh(
    response: Response,
    session: SessionDep,
    settings: SettingsDep,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
) -> UserProfile:
    if refresh_token is None:
        raise AuthenticationError("Your session is no longer valid. Please sign in again.")

    user, pair = await SessionService(session, settings).rotate(refresh_token)
    set_session_cookies(
        response,
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        settings=settings,
    )
    return UserProfile.model_validate(user)
