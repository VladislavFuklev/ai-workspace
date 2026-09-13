"""Session issuing, rotation and revocation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession as DbSession

from ai_workspace_api.core.errors import AuthenticationError
from ai_workspace_api.core.logging import get_logger
from ai_workspace_api.core.settings import Settings
from ai_workspace_api.core.tokens import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)
from ai_workspace_api.models import Session, User
from ai_workspace_api.repositories.session import SessionRepository

logger = get_logger(__name__)

# Same sentence as a failed sign-in: "your session is invalid" and "your session
# was revoked because someone replayed your token" are not the client's business.
INVALID_SESSION = "Your session is no longer valid. Please sign in again."


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    session_id: uuid.UUID


class SessionService:
    def __init__(self, db: DbSession, settings: Settings) -> None:
        self._db = db
        self._settings = settings
        self._sessions = SessionRepository(db)

    async def issue(self, user: User, *, family_id: uuid.UUID | None = None) -> TokenPair:
        """Creates a session and its token pair.

        A new sign-in starts a new family; a rotation continues the existing one,
        which is what lets a replay be traced back to every token that came from
        the same original sign-in.
        """
        refresh_token = create_refresh_token()
        session = Session(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            family_id=family_id or uuid.uuid4(),
            expires_at=datetime.now(UTC) + timedelta(days=self._settings.refresh_token_ttl_days),
        )
        self._sessions.add(session)
        await self._db.flush()

        access_token = create_access_token(
            user_id=user.id,
            session_id=session.id,
            secret=self._settings.session_secret.get_secret_value(),
            ttl_seconds=self._settings.access_token_ttl_seconds,
        )
        return TokenPair(access_token, refresh_token, session.id)

    async def rotate(self, refresh_token: str) -> tuple[User, TokenPair]:
        """Exchanges a refresh token for a new pair, or raises.

        Rotation is what makes theft survivable: a stolen token works once, and
        the moment either party uses the retired one the family is destroyed and
        both are signed out. That is noisy on purpose — a silent theft is worse.
        """
        existing = await self._sessions.get_by_token_hash(hash_refresh_token(refresh_token))

        if existing is None:
            logger.info("refresh rejected", reason="unknown_token")
            raise AuthenticationError(INVALID_SESSION)

        if existing.revoked_at is not None:
            if await self._is_concurrent_refresh(existing):
                # A second browser tab, not a thief: the token was retired
                # moments ago and its successor is still live.
                logger.info(
                    "concurrent refresh within the grace window",
                    family_id=str(existing.family_id),
                )
            else:
                revoked = await self._sessions.revoke_family(existing.family_id)
                await self._db.commit()
                logger.warning(
                    "refresh token reuse detected; family revoked",
                    family_id=str(existing.family_id),
                    user_id=str(existing.user_id),
                    sessions_revoked=revoked,
                )
                raise AuthenticationError(INVALID_SESSION)

        if existing.expires_at <= datetime.now(UTC):
            logger.info("refresh rejected", reason="expired", user_id=str(existing.user_id))
            raise AuthenticationError(INVALID_SESSION)

        user = await self._db.get(User, existing.user_id)
        if user is None or not user.is_active:
            logger.info("refresh rejected", reason="user_unavailable")
            raise AuthenticationError(INVALID_SESSION)

        existing.revoked_at = datetime.now(UTC)
        pair = await self.issue(user, family_id=existing.family_id)
        await self._db.commit()
        logger.info("session rotated", user_id=str(user.id))
        return user, pair

    async def _is_concurrent_refresh(self, retired: Session) -> bool:
        """Whether a retired token is a second tab rather than a replay.

        Both conditions matter. Recently retired alone is not enough — a thief
        who moves fast would qualify. The family must also still have a live
        session, which means the legitimate rotation is the one that retired it
        and nothing has gone wrong since.
        """
        grace = timedelta(seconds=self._settings.refresh_grace_seconds)
        if grace.total_seconds() == 0 or retired.revoked_at is None:
            return False
        if datetime.now(UTC) - retired.revoked_at > grace:
            return False
        return await self._sessions.has_live_session_in_family(retired.family_id)

    async def revoke_session(self, session_id: uuid.UUID) -> None:
        session = await self._db.get(Session, session_id)
        if session is not None and session.revoked_at is None:
            session.revoked_at = datetime.now(UTC)
            await self._db.commit()

    async def revoke_all(self, user_id: uuid.UUID) -> int:
        count = await self._sessions.revoke_all_for_user(user_id)
        await self._db.commit()
        logger.info("all sessions revoked", user_id=str(user_id), sessions_revoked=count)
        return count
