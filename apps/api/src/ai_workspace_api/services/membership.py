"""Membership rules and the only place a `TenantScope` is created."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.core.errors import ConflictError, NotFoundError, PermissionDeniedError
from ai_workspace_api.core.logging import get_logger
from ai_workspace_api.core.permissions import ROLE_RANK, Permission
from ai_workspace_api.core.tenancy import TenantScope
from ai_workspace_api.models import Membership, Organization, Role, User
from ai_workspace_api.repositories.membership import MembershipRepository

logger = get_logger(__name__)

# Deliberately the same message as a genuinely missing organisation. Saying
# "you are not a member of this organisation" confirms it exists, which turns
# a URL into a way to discover other tenants.
NO_ACCESS = "That workspace does not exist."
LAST_OWNER = "An organisation must keep at least one owner. Make someone else an owner first."
OWN_ROLE = "You cannot change your own role. Ask another owner or administrator."
SELF_REMOVE = "You cannot remove yourself. Leave the organisation instead."
ABOVE_OWN_LEVEL = "You cannot grant a role above your own."


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

    async def change_role(
        self, actor: TenantScope, target_user_id: uuid.UUID, role: Role
    ) -> Membership:
        """Changes a member's role, or refuses.

        Four rules, each of which exists because of a specific way this goes
        wrong:

        1. The actor needs the permission at all.
        2. **Nobody changes their own role** — including an owner, because
           "demote yourself by accident" is how an organisation loses its last
           administrator.
        3. **Nobody grants above their own level.** Without it an admin promotes
           themselves to owner via a second account, and the ladder means nothing.
        4. **The last owner cannot be demoted.** An organisation with no owner
           cannot be deleted, transferred, or have its billing changed.
        """
        actor.require(Permission.MEMBER_ROLE_CHANGE)

        if actor.user_id == target_user_id:
            raise PermissionDeniedError(OWN_ROLE)

        if ROLE_RANK[role] > ROLE_RANK[actor.role]:
            raise PermissionDeniedError(ABOVE_OWN_LEVEL)

        membership = await self._memberships.get(target_user_id, actor.organization_id)
        if membership is None:
            raise NotFoundError("That person is not a member of this workspace.")

        # Acting on someone above you is the same problem as granting above your
        # level, from the other direction.
        if ROLE_RANK[membership.role] > ROLE_RANK[actor.role]:
            raise PermissionDeniedError(ABOVE_OWN_LEVEL)

        if membership.role is Role.OWNER and role is not Role.OWNER:
            await self._require_another_owner(actor.organization_id, membership.user_id)

        membership.role = role
        await self._session.flush()
        logger.info(
            "member role changed",
            organization_id=str(actor.organization_id),
            target_user_id=str(target_user_id),
            role=role.value,
        )
        return membership

    async def remove_member(self, actor: TenantScope, target_user_id: uuid.UUID) -> None:
        """Removes someone from the organisation, or refuses.

        The same ladder rules as a role change, plus the last-owner guard —
        removing the last owner strands the organisation exactly as demoting
        them would.
        """
        actor.require(Permission.MEMBER_REMOVE)

        if actor.user_id == target_user_id:
            # Leaving is a different act with different rules; routing it
            # through here would let an admin "leave" while skipping none of the
            # permission checks but all of the intent.
            raise PermissionDeniedError(SELF_REMOVE)

        membership = await self._memberships.get(target_user_id, actor.organization_id)
        if membership is None:
            raise NotFoundError("That person is not a member of this workspace.")

        if ROLE_RANK[membership.role] > ROLE_RANK[actor.role]:
            raise PermissionDeniedError(ABOVE_OWN_LEVEL)

        if membership.role is Role.OWNER:
            await self._require_another_owner(actor.organization_id, membership.user_id)

        await self._session.delete(membership)
        await self._session.flush()
        logger.info(
            "member removed",
            organization_id=str(actor.organization_id),
            target_user_id=str(target_user_id),
        )

    async def leave(self, scope: TenantScope) -> None:
        """Removes the caller from the organisation.

        Leaving is not `remove_member` with yourself as the target: it needs no
        permission — a viewer may leave — but it keeps the last-owner guard,
        because an organisation whose last owner walks out is stranded exactly
        as it would be if someone else removed them.
        """
        membership = await self._memberships.get(scope.user_id, scope.organization_id)
        if membership is None:
            raise NotFoundError(NO_ACCESS)

        if membership.role is Role.OWNER:
            await self._require_another_owner(scope.organization_id, scope.user_id)

        await self._session.delete(membership)
        await self._session.flush()
        logger.info(
            "member left",
            organization_id=str(scope.organization_id),
            user_id=str(scope.user_id),
        )

    async def _require_another_owner(
        self, organization_id: uuid.UUID, excluding_user_id: uuid.UUID
    ) -> None:
        members = await self._memberships.list_for_organization(organization_id)
        other_owners = [
            m for m in members if m.role is Role.OWNER and m.user_id != excluding_user_id
        ]
        if not other_owners:
            raise ConflictError(LAST_OWNER)
