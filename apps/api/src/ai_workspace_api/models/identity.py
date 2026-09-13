"""External identities.

One row per (provider, subject) pair. The subject is the provider's own opaque
id for the person — not their email, which they can change and which some
providers let users choose freely.
"""

from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from ai_workspace_api.models.base import Base, Timestamps, UUIDPrimaryKey


class IdentityProvider(StrEnum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GITHUB = "github"


class Identity(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "identities"

    __table_args__ = (
        # The pair is the identity. Subject alone is not unique across providers,
        # and two providers can and do use the same-looking ids.
        Index("uq_identities_provider_subject", "provider", "subject", unique=True),
        Index("ix_identities_user_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[IdentityProvider] = mapped_column(
        Enum(IdentityProvider, name="identity_provider"), nullable=False
    )
    # Opaque and provider-assigned. Not the email: an email can be reassigned to
    # a different person after an employee leaves, and linking on it would hand
    # the new holder the old one's account.
    subject: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"<Identity {self.provider} user={self.user_id}>"
