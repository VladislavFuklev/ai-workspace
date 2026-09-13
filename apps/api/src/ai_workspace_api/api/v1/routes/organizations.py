"""Organisation endpoints.

Every route below the collection carries the organisation's slug, so the tenant
is visible in the URL, in access logs and in a bug report — and the scope is
resolved by the framework before the handler runs.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, status

from ai_workspace_api.api.auth_dependencies import CurrentPrincipal
from ai_workspace_api.api.dependencies import SessionDep
from ai_workspace_api.api.tenant_dependencies import require_permission
from ai_workspace_api.core.errors import NotFoundError
from ai_workspace_api.core.permissions import Permission
from ai_workspace_api.core.tenancy import TenantScope
from ai_workspace_api.repositories import MembershipRepository, OrganizationRepository
from ai_workspace_api.schemas.organization import (
    CreateOrganizationRequest,
    MemberSummary,
    OrganizationSummary,
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
    return OrganizationSummary(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        role=(await MembershipService(session).resolve_scope(principal.user, organization.id)).role,
    )


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
        OrganizationSummary(
            id=organization.id, name=organization.name, slug=organization.slug, role=membership.role
        )
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
    return OrganizationSummary(
        id=organization.id, name=organization.name, slug=organization.slug, role=scope.role
    )


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
