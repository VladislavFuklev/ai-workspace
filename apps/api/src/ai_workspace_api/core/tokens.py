"""Access and refresh tokens.

Two different things with two different jobs:

- **Access token** — a signed JWT, short-lived, checked without touching the
  database. It cannot be revoked before it expires, which is why it is short.
- **Refresh token** — opaque randomness, stored hashed, checked against the
  database. It can be revoked, and it is the only thing that can mint a new
  access token.

Splitting them is what makes both "most requests need no database read" and
"a session can be ended" true at once.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

ALGORITHM = "HS256"
# 256 bits. token_urlsafe counts bytes, not characters.
REFRESH_TOKEN_BYTES = 32


class InvalidTokenError(Exception):
    """The token is missing, malformed, expired, or not the kind expected."""


def create_access_token(
    *, user_id: uuid.UUID, session_id: uuid.UUID, secret: str, ttl_seconds: int
) -> str:
    """A JWT carrying who and which session, and nothing else.

    No email, no name, no roles: a JWT is base64, not encryption, and anything in
    it is readable by whoever holds it. It also goes stale — a role revoked a
    minute ago would still be in a token issued two minutes ago.
    """
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "sid": str(session_id),
        # Distinguishes an access token from anything else signed with this key,
        # so one cannot be presented where another is expected.
        "typ": "access",
        "iat": now,
        "exp": now + timedelta(seconds=ttl_seconds),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_access_token(token: str, *, secret: str) -> tuple[uuid.UUID, uuid.UUID]:
    """Returns `(user_id, session_id)` or raises `InvalidTokenError`.

    `algorithms` is pinned: accepting whatever the token's header claims is the
    classic JWT forgery, including `alg: none`.
    """
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError as error:
        raise InvalidTokenError(str(error)) from error

    if payload.get("typ") != "access":
        raise InvalidTokenError("not an access token")
    try:
        return uuid.UUID(payload["sub"]), uuid.UUID(payload["sid"])
    except (KeyError, ValueError) as error:
        raise InvalidTokenError("malformed claims") from error


def create_refresh_token() -> str:
    """Opaque randomness. It means nothing on its own; only the row it hashes to."""
    return secrets.token_urlsafe(REFRESH_TOKEN_BYTES)


def hash_refresh_token(token: str) -> str:
    """SHA-256 hex, to match the 64-character column.

    Deliberately not Argon2. The token is 256 bits of randomness, so there is no
    dictionary attack to slow down, and a slow hash would cost 50ms on every
    refresh for nothing.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
