"""Authentication request and response shapes."""

from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

from ai_workspace_api.schemas.password import Password


class RegisterRequest(BaseModel):
    # EmailStr validates the format; `normalize_email` decides how it is stored.
    email: EmailStr
    password: Password
    display_name: Annotated[str, Field(min_length=1, max_length=100)]


class RegisterResponse(BaseModel):
    """Deliberately says nothing about what happened.

    The same body is returned whether an account was created or the address was
    already registered, so the response cannot be used to test whether an address
    exists (ADR-018).
    """

    message: str = "Check your email to finish setting up your account."


class UserProfile(BaseModel):
    """The user as the client sees them. No password hash, no internal flags
    beyond what the interface actually needs."""

    id: uuid.UUID
    email: EmailStr
    display_name: str
    is_verified: bool

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    # Not the `Password` policy type: an existing password predates any policy
    # change, and refusing to *check* it would lock people out of their accounts.
    email: EmailStr
    password: Annotated[str, Field(min_length=1, max_length=1024)]


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetResponse(BaseModel):
    """Says the same thing whether or not the address has an account."""

    message: str = "If that address has an account, a reset link is on its way."


class PasswordResetConfirm(BaseModel):
    token: Annotated[str, Field(min_length=16, max_length=256)]
    # The policy applies here: this is a password being *chosen*, unlike sign-in.
    password: Password
