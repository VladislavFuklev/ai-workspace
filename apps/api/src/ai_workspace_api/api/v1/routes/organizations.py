"""Organisation endpoints.

Every route below the collection carries the organisation's slug, so the tenant
is visible in the URL, in access logs and in a bug report — and the scope is
resolved by the framework before the handler runs.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, status

from ai_workspace_api.api.auth_dependencies import CurrentPrincipal
from ai_workspace_api.api.dependencies import SessionDep
from ai_workspace_api.api.tenant_dependencies import TenantScopeDep, require_permission
from ai_workspace_api.core.errors import NotFoundError
from ai_workspace_api.core.permissions import Permission
from ai_workspace_api.core.tenancy import TenantScope
from ai_workspace_api.repositories import (
    MembershipRepository,
    OrganizationRepository,
    UserRepository,
)
from ai_workspace_api.schemas.organization import (
    ChangeRoleRequest,
    CreateOrganizationRequest,
    MemberSummary,
    OrganizationSummary,
    UpdateOrganizationRequest,
)
from ai_workspace_api.services import MembershipService, OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post(
    "",
    name="create_organization",
    status_code=status.HTTP_201_CREATED,
    response_model=OrganizationSummary,
    summary="Create an organisation",
    description="The caller becomes its owner. Any signed-in user may create one.",
)
async def create_organization(
    payload: CreateOrganizationRequest,
    principal: CurrentPrincipal,
    session: SessionDep,
) -> OrganizationSummary:
    # No permission check: there is no organisation to have a role in yet.
    organization = await OrganizationService(session).create(payload.name, principal.user)
    await session.commit()
    role = (await MembershipService(session).resolve_scope(principal.user, organization.id)).role
    return OrganizationSummary.of(organization, role)


@router.get(
    "",
    name="list_organizations",
    response_model=list[OrganizationSummary],
    summary="Organisations you belong to",
    description="Only the caller's own. There is no endpoint that lists all of them.",
)
async def list_organizations(
    principal: CurrentPrincipal, session: SessionDep
) -> list[OrganizationSummary]:
    memberships = await MembershipService(session).list_for_user(principal.user)
    return [
        OrganizationSummary.of(organization, membership.role)
        for membership, organization in memberships
    ]


@router.get(
    "/{organization_slug}",
    name="read_organization",
    response_model=OrganizationSummary,
    summary="One organisation",
    description="404 for a non-member, identically to a slug that does not exist.",
)
async def read_organization(
    scope: Annotated[TenantScope, require_permission(Permission.ORGANIZATION_READ)],
    session: SessionDep,
) -> OrganizationSummary:
    organization = await OrganizationRepository(session).get_by_id(scope.organization_id)
    if organization is None:
        # Unreachable: the scope was resolved from this organisation. Written as
        # a check rather than an assert, which `python -O` strips.
        raise NotFoundError("That workspace does not exist.")
    return OrganizationSummary.of(organization, scope.role)


@router.get(
    "/{organization_slug}/members",
    name="list_members",
    response_model=list[MemberSummary],
    summary="Members of an organisation",
)
async def list_members(
    scope: Annotated[TenantScope, require_permission(Permission.MEMBER_READ)],
    session: SessionDep,
) -> list[MemberSummary]:
    rows = await MembershipRepository(session).list_members_with_users(scope.organization_id)
    return [
        MemberSummary(
            user_id=user.id,
            email=user.email,
            display_name=user.display_name,
            role=membership.role,
        )
        for membership, user in rows
    ]


@router.patch(
    "/{organization_slug}",
    name="update_organization",
    response_model=OrganizationSummary,
    summary="Rename an organisation",
    description="The address does not change: links people already hold keep working.",
)
async def update_organization(
    payload: UpdateOrganizationRequest,
    scope: Annotated[TenantScope, require_permission(Permission.ORGANIZATION_UPDATE)],
    session: SessionDep,
) -> OrganizationSummary:
    organization = await OrganizationService(session).rename(scope, payload.name)
    await session.commit()
    return OrganizationSummary.of(organization, scope.role)


@router.delete(
    "/{organization_slug}",
    name="delete_organization",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an organisation",
    description="Owners only. Its memberships go with it.",
)
async def delete_organization(
    scope: Annotated[TenantScope, require_permission(Permission.ORGANIZATION_DELETE)],
    session: SessionDep,
) -> None:
    await OrganizationService(session).delete(scope)
    await session.commit()


@router.patch(
    "/{organization_slug}/members/{user_id}",
    name="change_member_role",
    response_model=MemberSummary,
    summary="Change a member's role",
    description=(
        "Refused for your own role, for a role above your own, for someone above "
        "you, and for the organisation's last owner."
    ),
)
async def change_member_role(
    user_id: uuid.UUID,
    payload: ChangeRoleRequest,
    scope: Annotated[TenantScope, require_permission(Permission.MEMBER_ROLE_CHANGE)],
    session: SessionDep,
) -> MemberSummary:
    memberships = MembershipService(session)
    membership = await memberships.change_role(scope, user_id, payload.role)
    await session.commit()

    user = await UserRepository(session).get_by_id(membership.user_id)
    if user is None:
        raise NotFoundError("That person is not a member of this workspace.")
    return MemberSummary(
        user_id=user.id, email=user.email, display_name=user.display_name, role=membership.role
    )


@router.delete(
    "/{organization_slug}/members/me",
    name="leave_organization",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Leave an organisation",
    description="Any member may leave. The last owner may not, until someone else is one.",
)
# Declared before `/members/{user_id}`: routes match in order, and "me" would
# otherwise be parsed as a UUID and rejected before reaching a handler.
async def leave_organization(scope: TenantScopeDep, session: SessionDep) -> None:
    await MembershipService(session).leave(scope)
    await session.commit()


@router.delete(
    "/{organization_slug}/members/{user_id}",
    name="remove_member",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member",
    description="Not yourself — use the leave endpoint, which needs no permission.",
)
async def remove_member(
    user_id: uuid.UUID,
    scope: Annotated[TenantScope, require_permission(Permission.MEMBER_REMOVE)],
    session: SessionDep,
) -> None:
    await MembershipService(session).remove_member(scope, user_id)
    await session.commit()
