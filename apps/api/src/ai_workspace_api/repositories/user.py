"""Data access for users.

The only layer that talks to the database about users. It holds no rules about
who may sign in — that belongs to a service — and it never commits: the caller
owns the transaction boundary (task 2.3).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.models import User


def normalize_email(email: str) -> str:
    """The single definition of what an address looks like in storage.

    Lowercased and trimmed. The local part of an address is technically
    case-sensitive, but no provider people actually use treats it that way, and
    two accounts differing only by case is an account-takeover vector. The
    database enforces the same rule with a functional unique index, so a caller
    that forgets this still cannot create the duplicate.
    """
    return email.strip().lower()


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        """Case-insensitive by construction: the stored value is normalised."""
        result = await self._session.execute(
            select(User).where(User.email == normalize_email(email))
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        result = await self._session.execute(
            select(User.id).where(User.email == normalize_email(email)).limit(1)
        )
        return result.first() is not None

    def add(self, user: User) -> User:
        """Stages the row. Flushing and committing are the caller's decision."""
        self._session.add(user)
        return user
