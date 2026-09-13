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
