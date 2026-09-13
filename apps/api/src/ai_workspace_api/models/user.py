"""The user table.

Email is the identity. There is no separate username: one fewer thing to make
unique, to recover, and to display inconsistently.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from ai_workspace_api.models.base import Base, Timestamps, UUIDPrimaryKey


class User(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "users"

    __table_args__ = (
        # A functional unique index, not a plain one on the column. Addresses are
        # normalised to lowercase on the way in, but "we always remember to
        # normalise" is not a guarantee — and two accounts differing only by case
        # is an account-takeover vector, not a tidiness problem. The database
        # refuses it whatever the application does.
        # `text`, not `func.lower("email")` — the latter compiles to
        # lower('email'), an index on a constant that protects nothing.
        Index("uq_users_email_lower", text("lower(email)"), unique=True),
    )

    email: Mapped[str] = mapped_column(
        String(320),  # the longest address RFC 5321 allows
        nullable=False,
    )

    # Nullable on purpose: a user who signed up through an identity provider
    # (task 3.8) has no password. A sentinel value would have to be excluded
    # everywhere a password is checked, and one missed check is an auth bypass.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Separate from `is_verified` because they answer different questions.
    # `is_active` is whether an administrator has disabled the account;
    # `is_verified` is whether the email address has been proven.
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    def __repr__(self) -> str:
        # No email: a repr reaches logs and tracebacks, and an address is
        # personal data.
        return f"<User {self.id}>"
