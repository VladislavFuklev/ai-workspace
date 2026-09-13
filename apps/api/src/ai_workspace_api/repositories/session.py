"""Data access for refresh sessions."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import CursorResult, select, update
from sqlalchemy.ext.asyncio import AsyncSession as DbSession

from ai_workspace_api.models import Session


class SessionRepository:
    def __init__(self, session: DbSession) -> None:
        self._db = session

    async def get_by_token_hash(self, token_hash: str) -> Session | None:
        """Returns the row even when revoked or expired.

        The caller needs to tell "no such token" from "a token that was rotated
        away" — the second is a replay and revokes the family.
        """
        result = await self._db.execute(select(Session).where(Session.token_hash == token_hash))
        return result.scalar_one_or_none()

    def add(self, session: Session) -> Session:
        self._db.add(session)
        return session

    async def revoke_family(self, family_id: uuid.UUID) -> int:
        """Ends every session descended from one sign-in. Returns how many."""
        # `execute` is typed as returning Result, but an UPDATE always yields a
        # CursorResult; rowcount is the only way to report what was affected
        # without a second query.
        result: CursorResult[Any] = await self._db.execute(  # type: ignore[assignment]
            update(Session)
            .where(Session.family_id == family_id, Session.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        return result.rowcount

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        result: CursorResult[Any] = await self._db.execute(  # type: ignore[assignment]
            update(Session)
            .where(Session.user_id == user_id, Session.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        return result.rowcount

    async def count_live_for_user(self, user_id: uuid.UUID) -> int:
        result = await self._db.execute(
            select(Session).where(
                Session.user_id == user_id,
                Session.revoked_at.is_(None),
                Session.expires_at > datetime.now(UTC),
            )
        )
        return len(result.scalars().all())
