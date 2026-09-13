"""Password reset.

Two endpoints' worth of rules. The important one is what happens *after* a
successful reset: every session ends. A reset is what someone does when they
believe their account is compromised, and leaving the intruder signed in is the
one outcome the flow must not produce.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession as DbSession

from ai_workspace_api.core.errors import ValidationError
from ai_workspace_api.core.logging import get_logger
from ai_workspace_api.core.passwords import hash_password
from ai_workspace_api.core.settings import Settings
from ai_workspace_api.core.tokens import create_refresh_token, hash_refresh_token
from ai_workspace_api.models import PasswordResetToken, User
from ai_workspace_api.repositories import UserRepository
from ai_workspace_api.services.session import SessionService

logger = get_logger(__name__)

# Short: long enough to read an email and act, short enough that a token sitting
# in an inbox or a proxy log is not a standing key to the account.
TOKEN_TTL = timedelta(hours=1)

# The same sentence for an unknown, expired, used or foreign token. Telling them
# apart tells an attacker which of their guesses was closest.
INVALID_LINK_MESSAGE = "That reset link is no longer valid. Request a new one."


class PasswordResetService:
    def __init__(self, db: DbSession, settings: Settings) -> None:
        self._db = db
        self._settings = settings
        self._users = UserRepository(db)

    async def request(self, email: str) -> str | None:
        """Issues a token, or does nothing when the address is unknown.

        Returns the raw token so the caller can send it. The endpoint answers
        identically either way — the return value is for the email, not the
        response (the same rule as registration, ADR-018).
        """
        user = await self._users.get_by_email(email)
        if user is None:
            logger.info("reset requested for an unknown address")
            return None

        # One live token at a time: an older link left in an inbox should stop
        # working the moment a newer one is requested.
        await self._invalidate_outstanding(user)

        raw = create_refresh_token()
        self._db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_refresh_token(raw),
                expires_at=datetime.now(UTC) + TOKEN_TTL,
            )
        )
        await self._db.commit()
        logger.info("reset token issued", user_id=str(user.id))
        return raw

    async def confirm(self, raw_token: str, new_password: str) -> User:
        """Applies the new password, or raises `ValidationError`."""
        record = (
            await self._db.execute(
                select(PasswordResetToken).where(
                    PasswordResetToken.token_hash == hash_refresh_token(raw_token)
                )
            )
        ).scalar_one_or_none()

        if record is None or record.used_at is not None:
            logger.info("reset rejected", reason="unknown_or_used")
            raise ValidationError(INVALID_LINK_MESSAGE)

        if record.expires_at <= datetime.now(UTC):
            logger.info("reset rejected", reason="expired", user_id=str(record.user_id))
            raise ValidationError(INVALID_LINK_MESSAGE)

        user = await self._db.get(User, record.user_id)
        if user is None or not user.is_active:
            logger.info("reset rejected", reason="user_unavailable")
            raise ValidationError(INVALID_LINK_MESSAGE)

        user.password_hash = hash_password(new_password)
        record.used_at = datetime.now(UTC)
        await self._invalidate_outstanding(user)

        # The whole point of the flow. Anyone already signed in with the old
        # password — including whoever prompted the reset — is signed out.
        revoked = await SessionService(self._db, self._settings).revoke_all(user.id)

        await self._db.commit()
        logger.info("password reset", user_id=str(user.id), sessions_revoked=revoked)
        return user

    async def _invalidate_outstanding(self, user: User) -> None:
        await self._db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
        )
