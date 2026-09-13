"""Linking a provider identity to an account.

The seam an OAuth flow plugs into: once a provider has been verified and has
handed back a profile, this decides which user that profile is.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession as DbSession

from ai_workspace_api.core.errors import ConflictError
from ai_workspace_api.core.logging import get_logger
from ai_workspace_api.models import Identity, IdentityProvider, User
from ai_workspace_api.repositories import UserRepository, normalize_email

logger = get_logger(__name__)

ALREADY_REGISTERED = (
    "An account already exists for that email address. Sign in with your "
    "password first, then connect this provider from your settings."
)


@dataclass(frozen=True)
class ProviderProfile:
    """What an OAuth callback produces, after the provider has been verified."""

    provider: IdentityProvider
    subject: str
    email: str
    display_name: str
    # Whether the *provider* vouches for the address. Some do not, and an
    # unverified one must never be treated as proof of anything.
    email_verified: bool


class IdentityService:
    def __init__(self, db: DbSession) -> None:
        self._db = db
        self._users = UserRepository(db)

    async def sign_in(self, profile: ProviderProfile) -> User:
        """Returns the user for a verified provider profile.

        Three cases, and the third is the one that matters:

        1. The identity is known — return its user.
        2. Nothing matches — create a user with no password.
        3. **The email matches an existing account but the identity does not.**
           Linking automatically would mean anyone who can get a provider to
           assert an address takes over the account behind it. It is refused, and
           the user is told to sign in and link deliberately (ADR-020).
        """
        existing = await self._find_identity(profile.provider, profile.subject)
        if existing is not None:
            logger.info("provider sign-in", provider=profile.provider, linked=True)
            return existing

        email = normalize_email(profile.email)
        if await self._users.email_exists(email):
            logger.info(
                "provider sign-in refused: address belongs to an existing account",
                provider=profile.provider,
            )
            raise ConflictError(ALREADY_REGISTERED)

        user = User(
            email=email,
            # No password: that is what the nullable column in 3.1 is for.
            password_hash=None,
            display_name=profile.display_name.strip() or email.split("@")[0],
            # Only if the provider actually vouches for it.
            is_verified=profile.email_verified,
        )
        self._users.add(user)
        await self._db.flush()

        self._db.add(Identity(user_id=user.id, provider=profile.provider, subject=profile.subject))
        await self._db.commit()
        await self._db.refresh(user)
        logger.info("user created from provider", provider=profile.provider, user_id=str(user.id))
        return user

    async def link_to_existing(self, user: User, profile: ProviderProfile) -> Identity:
        """Attaches a provider to an account the caller has already proved.

        Used from settings, where the user is signed in — which is the proof that
        `sign_in` cannot get and therefore refuses to assume.
        """
        if await self._find_identity(profile.provider, profile.subject) is not None:
            raise ConflictError("That provider account is already connected to a user.")

        identity = Identity(user_id=user.id, provider=profile.provider, subject=profile.subject)
        self._db.add(identity)
        await self._db.commit()
        logger.info("provider linked", provider=profile.provider, user_id=str(user.id))
        return identity

    async def _find_identity(self, provider: IdentityProvider, subject: str) -> User | None:
        result = await self._db.execute(
            select(User)
            .join(Identity, Identity.user_id == User.id)
            .where(Identity.provider == provider, Identity.subject == subject)
        )
        return result.scalar_one_or_none()
