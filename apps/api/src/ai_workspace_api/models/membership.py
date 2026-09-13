"""Memberships — who belongs to which organisation, and as what.

The join table that makes multi-tenancy real. Every authorisation question in
the product eventually reduces to "is there a row here, and what is its role".
"""

from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from ai_workspace_api.models.base import Base, Timestamps, UUIDPrimaryKey


class Role(StrEnum):
    """Ordered from most to least authority. Task 4.3 gives them meaning."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Membership(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "memberships"

    __table_args__ = (
        # One membership per person per organisation. Two rows would mean two
        # roles, and every permission check would have to decide which wins.
        Index("uq_memberships_user_organization", "user_id", "organization_id", unique=True),
        # Listing "my organisations" and "this organisation's members" are the
        # two queries this table exists for.
        Index("ix_memberships_user_id", "user_id"),
        Index("ix_memberships_organization_id", "organization_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[Role] = mapped_column(Enum(Role, name="membership_role"), nullable=False)

    def __repr__(self) -> str:
        return f"<Membership user={self.user_id} org={self.organization_id} {self.role}>"
