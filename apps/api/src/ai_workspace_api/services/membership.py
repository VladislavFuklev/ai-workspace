"""Membership rules and the only place a `TenantScope` is created."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.core.errors import NotFoundError
from ai_workspace_api.core.logging import get_logger
from ai_workspace_api.core.tenancy import TenantScope
from ai_workspace_api.models import Membership, Organization, Role, User
from ai_workspace_api.repositories.membership import MembershipRepository

logger = get_logger(__name__)

# Deliberately the same message as a genuinely missing organisation. Saying
# "you are not a member of this organisation" confirms it exists, which turns
# a URL into a way to discover other tenants.
NO_ACCESS = "That workspace does not exist."


class MembershipService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._memberships = MembershipRepository(session)

    async def resolve_scope(self, user: User, organization_id: uuid.UUID) -> TenantScope:
        """The only way to obtain a `TenantScope`.

        Raises `NotFoundError` when there is no membership — the same error as a
        non-existent organisation, so the two are indistinguishable from outside.
        """
        membership = await self._memberships.get(user.id, organization_id)
        if membership is None:
            logger.info(
                "tenant access refused", user_id=str(user.id), organization_id=str(organization_id)
            )
            raise NotFoundError(NO_ACCESS)
        return TenantScope(
            user_id=user.id, organization_id=membership.organization_id, role=membership.role
        )

    async def resolve_scope_by_slug(self, user: User, slug: str) -> TenantScope:
        membership = await self._memberships.get_by_slug(user.id, slug)
        if membership is None:
            logger.info("tenant access refused", user_id=str(user.id), slug=slug)
            raise NotFoundError(NO_ACCESS)
        return TenantScope(
            user_id=user.id, organization_id=membership.organization_id, role=membership.role
        )

    def add_member(self, organization: Organization, user: User, role: Role) -> Membership:
        """Stages a membership. The caller owns the transaction."""
        return self._memberships.add(
            Membership(user_id=user.id, organization_id=organization.id, role=role)
        )

    async def list_for_user(self, user: User) -> Sequence[tuple[Membership, Organization]]:
        return await self._memberships.list_for_user(user.id)
