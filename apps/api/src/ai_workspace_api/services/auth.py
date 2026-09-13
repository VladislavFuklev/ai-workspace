"""Authentication rules.

The service owns the transaction boundary and the decisions; the repository owns
the queries and never commits (task 2.3).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.core.errors import AuthenticationError
from ai_workspace_api.core.logging import get_logger
from ai_workspace_api.core.passwords import (
    hash_password,
    needs_rehash,
    verify_absent_user,
    verify_password,
)
from ai_workspace_api.models import User
from ai_workspace_api.repositories import UserRepository, normalize_email

logger = get_logger(__name__)

# One message for every way signing in can fail. Wording it as "or" rather than
# naming a cause is what keeps the endpoint from confirming an address exists.
GENERIC_FAILURE = "That email address and password do not match an account."


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

    async def authenticate(self, email: str, password: str) -> User:
        """Returns the user, or raises `AuthenticationError`.

        Every failure raises the *same* error. A wrong address, a wrong password,
        an account with no password because it came from an identity provider, and
        a disabled account are four different facts, and telling them apart is the
        caller's problem, not something to hand an attacker.

        The no-user branch still does hashing work, so the two do not differ by
        response time either (task 3.4).
        """
        user = await self._users.get_by_email(email)

        if user is None:
            verify_absent_user(password)
            logger.info("sign-in failed", reason="no_user")
            raise AuthenticationError(GENERIC_FAILURE)

        if not verify_password(password, user.password_hash):
            # Covers a wrong password and a null hash alike; verify_password
            # spends equivalent time on the null case.
            logger.info("sign-in failed", reason="bad_password", user_id=str(user.id))
            raise AuthenticationError(GENERIC_FAILURE)

        if not user.is_active:
            # Checked *after* the password, on purpose: checking it first would
            # make a disabled account answer faster than a wrong password and
            # reveal that the address exists.
            logger.info("sign-in failed", reason="inactive", user_id=str(user.id))
            raise AuthenticationError(GENERIC_FAILURE)

        await self._upgrade_hash_if_needed(user, password)
        logger.info("sign-in succeeded", user_id=str(user.id))
        return user

    async def _upgrade_hash_if_needed(self, user: User, password: str) -> None:
        """A successful sign-in is the only moment the plaintext is in hand, so
        it is the only moment the stored hash can be strengthened."""
        if user.password_hash is None or not needs_rehash(user.password_hash):
            return
        user.password_hash = hash_password(password)
        await self._session.commit()
        logger.info("password hash upgraded", user_id=str(user.id))
