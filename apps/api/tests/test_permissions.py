"""What each role may do — and, mostly, what it may not."""

from __future__ import annotations

import uuid
from itertools import pairwise

import pytest

from ai_workspace_api.core.errors import PermissionDeniedError
from ai_workspace_api.core.permissions import (
    ROLE_PERMISSIONS,
    ROLE_RANK,
    Permission,
    permissions_for,
)
from ai_workspace_api.core.tenancy import TenantScope
from ai_workspace_api.models import Role


def scope(role: Role) -> TenantScope:
    return TenantScope(user_id=uuid.uuid4(), organization_id=uuid.uuid4(), role=role)


def test_every_role_has_a_permission_set() -> None:
    """A role missing from the table would raise a KeyError at the first check,
    in production, on whichever endpoint got there first."""
    assert set(ROLE_PERMISSIONS) == set(Role)
    assert set(ROLE_RANK) == set(Role)


@pytest.mark.parametrize(
    ("role", "granted"),
    [
        (
            Role.VIEWER,
            {
                Permission.DOCUMENT_READ,
                Permission.CONVERSATION_USE,
                Permission.MEMBER_READ,
                Permission.ORGANIZATION_READ,
            },
        ),
        (
            Role.MEMBER,
            {
                Permission.DOCUMENT_READ,
                Permission.DOCUMENT_WRITE,
                Permission.DOCUMENT_DELETE,
                Permission.CONVERSATION_USE,
                Permission.MEMBER_READ,
                Permission.ORGANIZATION_READ,
            },
        ),
    ],
)
def test_the_lower_roles_have_exactly_what_they_should(
    role: Role, granted: set[Permission]
) -> None:
    """Asserted as an exact set. A subset check would pass while a role quietly
    gained something."""
    assert permissions_for(role) == granted


@pytest.mark.parametrize(
    ("role", "denied"),
    [
        (Role.VIEWER, Permission.DOCUMENT_WRITE),
        (Role.VIEWER, Permission.DOCUMENT_DELETE),
        (Role.VIEWER, Permission.MEMBER_INVITE),
        (Role.VIEWER, Permission.USAGE_READ),
        (Role.MEMBER, Permission.MEMBER_INVITE),
        (Role.MEMBER, Permission.MEMBER_REMOVE),
        (Role.MEMBER, Permission.MEMBER_ROLE_CHANGE),
        (Role.MEMBER, Permission.ORGANIZATION_UPDATE),
        (Role.MEMBER, Permission.USAGE_READ),
        (Role.ADMIN, Permission.ORGANIZATION_DELETE),
    ],
)
def test_what_each_role_cannot_do(role: Role, denied: Permission) -> None:
    """The negative cases. A permission system with only positive tests is
    decoration."""
    assert scope(role).can(denied) is False

    with pytest.raises(PermissionDeniedError):
        scope(role).require(denied)


def test_only_an_owner_can_delete_the_organisation() -> None:
    assert scope(Role.OWNER).can(Permission.ORGANIZATION_DELETE) is True
    for role in (Role.ADMIN, Role.MEMBER, Role.VIEWER):
        assert scope(role).can(Permission.ORGANIZATION_DELETE) is False


def test_permissions_grow_with_authority() -> None:
    """Each role has at least everything the one below it does. Not how the table
    is built — it is written out per role — so this is a real check that the
    ladder holds."""
    ladder = [Role.VIEWER, Role.MEMBER, Role.ADMIN, Role.OWNER]
    for lower, higher in pairwise(ladder):
        assert permissions_for(lower) <= permissions_for(higher), f"{higher} lost something"
        assert ROLE_RANK[lower] < ROLE_RANK[higher]


def test_a_refusal_says_what_is_missing() -> None:
    """So the user can ask an administrator for the right thing."""
    with pytest.raises(PermissionDeniedError) as caught:
        scope(Role.VIEWER).require(Permission.DOCUMENT_WRITE)

    assert "document:write" in str(caught.value)
