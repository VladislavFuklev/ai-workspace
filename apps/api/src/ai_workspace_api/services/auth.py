"""Authentication rules.

The service owns the transaction boundary and the decisions; the repository owns
the queries and never commits (task 2.3).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.core.logging import get_logger
from ai_workspace_api.core.passwords import hash_password
from ai_workspace_api.models import User
from ai_workspace_api.repositories import UserRepository, normalize_email

logger = get_logger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)

    async def register(self, email: str, password: str, display_name: str) -> User | None:
        """Creates an account, or does nothing if the address is already taken.

        Returns the new user, or `None` when the address existed. The caller
        answers the same way either way (ADR-018) — the return value is for
        logging and for the email that will follow, not for the response.

        The password is hashed before anything is written, so no code path holds
        a plaintext password and a database handle at the same time.
        """
        normalized = normalize_email(email)

        if await self._users.email_exists(normalized):
            # Not a warning: someone re-submitting a form is not an incident.
            logger.info("registration for an existing address", email_taken=True)
            return None

        user = User(
            email=normalized,
            password_hash=hash_password(password),
            display_name=display_name.strip(),
        )
        self._users.add(user)
        # The service commits: it is the only layer that knows the unit of work
        # is finished.
        await self._session.commit()
        await self._session.refresh(user)

        logger.info("user registered", user_id=str(user.id))
        return user
