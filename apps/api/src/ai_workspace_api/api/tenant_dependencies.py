"""Resolving and checking the tenant scope for a request.

A permission check written inside a handler body is one the next handler can
omit. Expressed as a dependency it cannot be: the route does not resolve without
it, so the check is part of the signature rather than a line someone remembers.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Path, params

from ai_workspace_api.api.auth_dependencies import CurrentPrincipal
from ai_workspace_api.api.dependencies import SessionDep
from ai_workspace_api.core.permissions import Permission
from ai_workspace_api.core.tenancy import TenantScope
from ai_workspace_api.services import MembershipService

# Matches the slug format organizations are created with (task 4.1).
SlugPath = Annotated[str, Path(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=60)]


async def get_tenant_scope(
    principal: CurrentPrincipal, session: SessionDep, organization_slug: SlugPath
) -> TenantScope:
    """The caller's verified membership of the organisation in the path.

    Raises `NotFoundError` for a non-member — the same as an organisation that
    does not exist, so a URL cannot be used to discover other tenants.
    """
    return await MembershipService(session).resolve_scope_by_slug(principal.user, organization_slug)


TenantScopeDep = Annotated[TenantScope, Depends(get_tenant_scope)]


def require_permission(permission: Permission) -> params.Depends:
    """A dependency that yields a scope already checked for one permission.

    Used as `scope: Annotated[TenantScope, require_permission(...)]` — it returns
    the `Depends` itself, so
    the handler receives a scope it knows is sufficient — there is no version of
    the handler that runs without the check.
    """

    async def dependency(scope: TenantScopeDep) -> TenantScope:
        scope.require(permission)
        return scope

    return params.Depends(dependency=dependency)
