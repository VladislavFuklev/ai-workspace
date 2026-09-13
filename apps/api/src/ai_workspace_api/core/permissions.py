"""What each role may do.

One table, so the answer to "who can do this" is in a single readable place
rather than spread across handlers as `if role == ...`.

The roles form a ladder, but the permission sets are written out per role rather
than derived from a rank. Deriving them makes it impossible to give one role a
capability another above it lacks, and hides which role actually gained a
permission when the table changes.
"""

from __future__ import annotations

from enum import StrEnum

from ai_workspace_api.models import Role


class Permission(StrEnum):
    # Documents (phase 5)
    DOCUMENT_READ = "document:read"
    DOCUMENT_WRITE = "document:write"
    DOCUMENT_DELETE = "document:delete"

    # The assistant (phase 7)
    CONVERSATION_USE = "conversation:use"

    # People
    MEMBER_READ = "member:read"
    MEMBER_INVITE = "member:invite"
    MEMBER_REMOVE = "member:remove"
    MEMBER_ROLE_CHANGE = "member:role_change"

    # The organisation itself
    ORGANIZATION_READ = "organization:read"
    ORGANIZATION_UPDATE = "organization:update"
    ORGANIZATION_DELETE = "organization:delete"

    # Usage and cost (phase 10)
    USAGE_READ = "usage:read"


_VIEWER = frozenset(
    {
        Permission.DOCUMENT_READ,
        Permission.CONVERSATION_USE,
        Permission.MEMBER_READ,
        Permission.ORGANIZATION_READ,
    }
)

# A member can add and change documents but not remove people or read the bill.
_MEMBER = _VIEWER | {Permission.DOCUMENT_WRITE, Permission.DOCUMENT_DELETE}

# An admin runs the workspace day to day: people and settings, but not the
# organisation's existence and not ownership.
_ADMIN = _MEMBER | {
    Permission.MEMBER_INVITE,
    Permission.MEMBER_REMOVE,
    Permission.MEMBER_ROLE_CHANGE,
    Permission.ORGANIZATION_UPDATE,
    Permission.USAGE_READ,
}

# Only an owner can end the organisation.
_OWNER = _ADMIN | {Permission.ORGANIZATION_DELETE}

ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.VIEWER: frozenset(_VIEWER),
    Role.MEMBER: frozenset(_MEMBER),
    Role.ADMIN: frozenset(_ADMIN),
    Role.OWNER: frozenset(_OWNER),
}

# Authority order, for "may this person act on that one". Used for role changes,
# not for permissions — those come from the table above.
ROLE_RANK: dict[Role, int] = {
    Role.VIEWER: 0,
    Role.MEMBER: 1,
    Role.ADMIN: 2,
    Role.OWNER: 3,
}


def permissions_for(role: Role) -> frozenset[Permission]:
    return ROLE_PERMISSIONS[role]
