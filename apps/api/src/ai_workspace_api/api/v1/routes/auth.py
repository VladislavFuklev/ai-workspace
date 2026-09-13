"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status

from ai_workspace_api.api.dependencies import SessionDep
from ai_workspace_api.schemas.auth import RegisterRequest, RegisterResponse
from ai_workspace_api.services.auth import AuthService

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
