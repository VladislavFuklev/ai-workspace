"""Refresh sessions.

One row per live refresh token. The token itself is never stored — only a hash —
so a database leak does not hand out live sessions.

`family_id` ties every token issued from one sign-in together. Rotation replaces
a token within its family; presenting a token that was already rotated away means
someone has a copy, and the whole family is revoked.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from ai_workspace_api.models.base import Base, Timestamps, UUIDPrimaryKey


class Session(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "sessions"

    __table_args__ = (
        # Every refresh is a lookup by hash, and revocation is a sweep by family.
        Index("ix_sessions_token_hash", "token_hash", unique=True),
        Index("ix_sessions_family_id", "family_id"),
        Index("ix_sessions_user_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # SHA-256 hex. A fast hash is right here and Argon2 would be wrong: the token
    # is 256 bits of randomness, so there is no dictionary to slow down, and
    # every refresh would otherwise cost 50ms for no benefit.
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    family_id: Mapped[uuid.UUID] = mapped_column(nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Set when the token is rotated away or the session is ended. Kept rather than
    # deleted: a reused token has to be recognisable *after* it stops working.
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Session {self.id} user={self.user_id}>"
