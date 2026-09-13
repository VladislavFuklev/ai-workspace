"""Data access for memberships."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.models import Membership, Organization


class MembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: uuid.UUID, organization_id: uuid.UUID) -> Membership | None:
        result = await self._session.execute(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, user_id: uuid.UUID, slug: str) -> Membership | None:
        """One query rather than "find the organisation, then check membership".

        Two queries would let a caller act on the first result before the second
        answered, which is exactly the shape of an isolation bug.
        """
        from sqlalchemy import func

        result = await self._session.execute(
            select(Membership)
            .join(Organization, Organization.id == Membership.organization_id)
            .where(Membership.user_id == user_id, func.lower(Organization.slug) == slug.lower())
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID) -> Sequence[tuple[Membership, Organization]]:
        result = await self._session.execute(
            select(Membership, Organization)
            .join(Organization, Organization.id == Membership.organization_id)
            .where(Membership.user_id == user_id)
            .order_by(Organization.name)
        )
        return [(m, o) for m, o in result.all()]

    async def list_for_organization(self, organization_id: uuid.UUID) -> Sequence[Membership]:
        result = await self._session.execute(
            select(Membership)
            .where(Membership.organization_id == organization_id)
            .order_by(Membership.created_at)
        )
        return list(result.scalars().all())

    def add(self, membership: Membership) -> Membership:
        self._session.add(membership)
        return membership
