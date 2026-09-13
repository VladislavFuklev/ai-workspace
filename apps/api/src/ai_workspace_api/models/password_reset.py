"""Password reset tokens.

Stored hashed, like refresh tokens and for the same reason: a database leak must
not hand out a way to take over accounts.

A used token is marked rather than deleted, so "already used" and "never existed"
stay distinguishable in the logs — the first is worth noticing, the second is not.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from ai_workspace_api.models.base import Base, Timestamps, UUIDPrimaryKey


class PasswordResetToken(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "password_reset_tokens"

    __table_args__ = (
        Index("ix_password_reset_tokens_token_hash", "token_hash", unique=True),
        Index("ix_password_reset_tokens_user_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<PasswordResetToken {self.id} user={self.user_id}>"
