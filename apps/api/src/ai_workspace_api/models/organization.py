"""Organisations — the tenant boundary.

Every row that belongs to a customer will reference one of these. The isolation
rules that keep one tenant out of another's data all reduce to a filter on this
id, so it is worth being strict about here.
"""

from __future__ import annotations

from sqlalchemy import Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from ai_workspace_api.models.base import Base, Timestamps, UUIDPrimaryKey


class Organization(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "organizations"

    __table_args__ = (
        # Case-insensitive, like the user email index and for the same reason:
        # `acme` and `Acme` in a URL would be two tenants that look like one.
        Index("uq_organizations_slug_lower", text("lower(slug)"), unique=True),
    )

    # Not unique. Two unrelated companies can both be called "Acme", and refusing
    # the second one is a support ticket, not a safeguard.
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    # What appears in a URL. Unique, because it addresses the tenant.
    slug: Mapped[str] = mapped_column(String(60), nullable=False)

    def __repr__(self) -> str:
        return f"<Organization {self.slug}>"
