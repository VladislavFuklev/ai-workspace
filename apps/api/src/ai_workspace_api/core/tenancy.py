"""The tenant scope.

Multi-tenant leaks do not come from someone deciding to skip a check. They come
from one query out of forty where the `WHERE organization_id = ...` was
forgotten, in a file nobody reviewed closely, six months later.

`TenantScope` is the alternative: a value that can only be produced by verifying
a membership, and that tenant-scoped repositories require in their constructor.
Forgetting to filter stops being possible, because a repository cannot be built
without one — the mistake becomes a type error instead of a data leak.

It is deliberately not a plain `uuid`. A bare id can be passed from anywhere,
including straight out of a request body, which is the leak with extra steps.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from ai_workspace_api.core.errors import PermissionDeniedError
from ai_workspace_api.core.permissions import Permission, permissions_for
from ai_workspace_api.models import Role


@dataclass(frozen=True, slots=True)
class TenantScope:
    """A membership that has been checked.

    Only `MembershipService.resolve_scope` constructs one. Nothing else should:
    the whole value of the type is that holding one means the check happened.
    """

    user_id: uuid.UUID
    organization_id: uuid.UUID
    role: Role

    def can(self, permission: Permission) -> bool:
        return permission in permissions_for(self.role)

    def require(self, permission: Permission) -> None:
        """Raises unless the role has the permission.

        403 rather than 404 here, unlike a non-member: the caller has already
        proved they belong to this organisation, so refusing by name tells them
        nothing they did not know and tells them what to ask an admin for.
        """
        if not self.can(permission):
            raise PermissionDeniedError(
                f"Your role does not allow this. Ask an administrator for {permission.value}."
            )
