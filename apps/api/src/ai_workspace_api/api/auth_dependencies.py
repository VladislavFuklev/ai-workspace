"""Who is calling.

Every protected endpoint from phase 4 onwards depends on this, so it is the one
place that decides what "signed in" means.

The access token is checked by signature and expiry only — no database read.
That is the point of the split in ADR-019, and the cost is that a session ended
a moment ago still passes here until the token expires. Anything that must take
effect immediately has to check the session row itself.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Cookie, Depends, Request

from ai_workspace_api.api.cookies import ACCESS_COOKIE
from ai_workspace_api.api.dependencies import SessionDep
from ai_workspace_api.core.errors import AuthenticationError
from ai_workspace_api.core.settings import Settings
from ai_workspace_api.core.tokens import InvalidTokenError, decode_access_token
from ai_workspace_api.models import User

# The same sentence for every reason a request is not authenticated.
NOT_SIGNED_IN = "You are not signed in."


class Principal:
    """The authenticated caller and the session they are using."""

    __slots__ = ("session_id", "user")

    def __init__(self, user: User, session_id: uuid.UUID) -> None:
        self.user = user
        self.session_id = session_id


async def get_principal(
    request: Request,
    db: SessionDep,
    access_token: Annotated[str | None, Cookie(alias=ACCESS_COOKIE)] = None,
) -> Principal:
    if access_token is None:
        raise AuthenticationError(NOT_SIGNED_IN)

    settings: Settings = request.app.state.settings
    try:
        user_id, session_id = decode_access_token(
            access_token, secret=settings.session_secret.get_secret_value()
        )
    except InvalidTokenError as error:
        raise AuthenticationError(NOT_SIGNED_IN) from error

    # One read, to confirm the user still exists and is still allowed in. A
    # disabled account must not keep working for the life of its access token.
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise AuthenticationError(NOT_SIGNED_IN)

    return Principal(user=user, session_id=session_id)


CurrentPrincipal = Annotated[Principal, Depends(get_principal)]
