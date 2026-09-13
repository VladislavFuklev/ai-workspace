"""Data access for organisations."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.models import Organization


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, organization_id: uuid.UUID) -> Organization | None:
        return await self._session.get(Organization, organization_id)

    async def get_by_slug(self, slug: str) -> Organization | None:
        """Case-insensitive, matching the functional index on the column."""
        result = await self._session.execute(
            select(Organization).where(func.lower(Organization.slug) == slug.lower())
        )
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        result = await self._session.execute(
            select(Organization.id).where(func.lower(Organization.slug) == slug.lower()).limit(1)
        )
        return result.first() is not None

    def add(self, organization: Organization) -> Organization:
        self._session.add(organization)
        return organization
