"""Renaming, deleting, role changes, removal and leaving — over HTTP.

The rules themselves are tested in `test_role_changes.py`. What is tested here is
that each one survives the trip through a route: the right status code, no
detail that names another tenant, and nothing reachable by a caller who should
not reach it.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from ai_workspace_api.models import Membership, Organization, Role

from .test_organization_endpoints import ORGS, Api, api, build, join, make_user, sign_in, workspace

# Re-exported so pytest resolves the fixtures, and ruff sees them used.
__all__ = ["api", "build", "join", "make_user", "sign_in", "workspace"]

pytestmark = pytest.mark.integration


async def members_of(api: Api, organization: Organization) -> list[Membership]:
    result = await api.db.execute(
        select(Membership).where(Membership.organization_id == organization.id)
    )
    return list(result.scalars().all())


# --- authentication and membership --------------------------------------------


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("PATCH", f"{ORGS}/anything"),
        ("DELETE", f"{ORGS}/anything"),
        ("PATCH", f"{ORGS}/anything/members/{uuid.uuid4()}"),
        ("DELETE", f"{ORGS}/anything/members/{uuid.uuid4()}"),
        ("DELETE", f"{ORGS}/anything/members/me"),
    ],
)
async def test_every_endpoint_refuses_a_signed_out_caller(api: Api, method: str, path: str) -> None:
    response = await api.client.request(method, path, json={"name": "X", "role": "member"})

    assert response.status_code == 401, response.text


@pytest.mark.parametrize(
    ("method", "suffix"),
    [
        ("PATCH", ""),
        ("DELETE", ""),
        ("PATCH", f"/members/{uuid.uuid4()}"),
        ("DELETE", f"/members/{uuid.uuid4()}"),
        ("DELETE", "/members/me"),
    ],
)
async def test_a_non_member_gets_not_found_everywhere(api: Api, method: str, suffix: str) -> None:
    """Not 403: a caller who is not in the organisation must not learn that it
    exists, whatever they try to do to it."""
    await workspace(api.db, "Private Co", "privateowner@example.com")
    await make_user(api.db, "outsider@example.com")
    await sign_in(api, "outsider@example.com")

    response = await api.client.request(
        method, f"{ORGS}/private-co{suffix}", json={"name": "X", "role": "member"}
    )

    assert response.status_code == 404, response.text
    assert response.json()["message"] == "That workspace does not exist."


# --- renaming and deleting ----------------------------------------------------


async def test_an_admin_can_rename_but_the_address_does_not_change(api: Api) -> None:
    organization, _ = await workspace(api.db, "Old Name", "renameowner@example.com")
    await join(api.db, organization, "renameadmin@example.com", Role.ADMIN)
    await sign_in(api, "renameadmin@example.com")

    response = await api.client.patch(f"{ORGS}/old-name", json={"name": "New Name"})

    assert response.status_code == 200, response.text
    assert response.json()["name"] == "New Name"
    # The slug is what every existing link, bookmark and remembered choice uses.
    assert response.json()["slug"] == "old-name"
    assert (await api.client.get(f"{ORGS}/old-name")).status_code == 200


async def test_a_member_cannot_rename(api: Api) -> None:
    organization, _ = await workspace(api.db, "Fixed Co", "fixedowner@example.com")
    await join(api.db, organization, "fixedmember@example.com", Role.MEMBER)
    await sign_in(api, "fixedmember@example.com")

    response = await api.client.patch(f"{ORGS}/fixed-co", json={"name": "Renamed"})

    assert response.status_code == 403, response.text
    assert "organization:update" in response.json()["message"]


async def test_only_an_owner_can_delete_and_the_memberships_go_too(api: Api) -> None:
    organization, _ = await workspace(api.db, "Doomed Co", "doomedowner@example.com")
    await join(api.db, organization, "doomedadmin@example.com", Role.ADMIN)

    await sign_in(api, "doomedadmin@example.com")
    refused = await api.client.delete(f"{ORGS}/doomed-co")

    await sign_in(api, "doomedowner@example.com")
    deleted = await api.client.delete(f"{ORGS}/doomed-co")

    assert refused.status_code == 403, refused.text
    assert deleted.status_code == 204, deleted.text
    assert await members_of(api, organization) == []
    assert await api.db.get(Organization, organization.id) is None


# --- role changes -------------------------------------------------------------


async def test_an_owner_can_promote_a_member(api: Api) -> None:
    organization, _ = await workspace(api.db, "Promote Co", "promoteowner@example.com")
    member = await join(api.db, organization, "promotemember@example.com", Role.MEMBER)
    await sign_in(api, "promoteowner@example.com")

    response = await api.client.patch(
        f"{ORGS}/promote-co/members/{member.id}", json={"role": "admin"}
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "user_id": str(member.id),
        "email": "promotemember@example.com",
        "display_name": "promotemember",
        "role": "admin",
    }


async def test_an_admin_cannot_promote_to_owner(api: Api) -> None:
    organization, _ = await workspace(api.db, "Ladder Co", "ladderowner@example.com")
    await join(api.db, organization, "ladderadmin@example.com", Role.ADMIN)
    member = await join(api.db, organization, "laddermember@example.com", Role.MEMBER)
    await sign_in(api, "ladderadmin@example.com")

    response = await api.client.patch(
        f"{ORGS}/ladder-co/members/{member.id}", json={"role": "owner"}
    )

    assert response.status_code == 403, response.text


async def test_nobody_can_change_their_own_role(api: Api) -> None:
    _, owner = await workspace(api.db, "Selfish Co", "selfowner@example.com")
    await sign_in(api, "selfowner@example.com")

    response = await api.client.patch(
        f"{ORGS}/selfish-co/members/{owner.id}", json={"role": "member"}
    )

    assert response.status_code == 403, response.text


async def test_the_last_owner_cannot_be_demoted(api: Api) -> None:
    organization, owner = await workspace(api.db, "Solo Co", "soloowner@example.com")
    second = await join(api.db, organization, "soloadmin@example.com", Role.OWNER)
    await sign_in(api, "soloadmin@example.com")

    demoted = await api.client.patch(f"{ORGS}/solo-co/members/{owner.id}", json={"role": "member"})
    # With one owner left, the same call is now refused.
    stranded = await api.client.patch(
        f"{ORGS}/solo-co/members/{second.id}", json={"role": "member"}
    )

    assert demoted.status_code == 200, demoted.text
    assert stranded.status_code == 403, stranded.text


async def test_someone_from_another_organisation_is_not_found(api: Api) -> None:
    """404, not 403: the actor may act on members, so the only true statement is
    that this person is not one — and nothing about where they do belong."""
    await workspace(api.db, "Here Co", "hereowner@example.com")
    other, stranger = await workspace(api.db, "There Co", "thereowner@example.com")
    await sign_in(api, "hereowner@example.com")

    response = await api.client.patch(
        f"{ORGS}/here-co/members/{stranger.id}", json={"role": "admin"}
    )

    assert response.status_code == 404, response.text
    assert str(other.id) not in response.text
    assert "there" not in response.text.lower()


async def test_an_unknown_role_is_rejected_before_any_rule_runs(api: Api) -> None:
    organization, _ = await workspace(api.db, "Enum Co", "enumowner@example.com")
    member = await join(api.db, organization, "enummember@example.com", Role.MEMBER)
    await sign_in(api, "enumowner@example.com")

    response = await api.client.patch(
        f"{ORGS}/enum-co/members/{member.id}", json={"role": "superuser"}
    )

    assert response.status_code == 422, response.text


# --- removal and leaving ------------------------------------------------------


async def test_an_admin_can_remove_a_member_but_not_an_owner(api: Api) -> None:
    organization, owner = await workspace(api.db, "Exit Co", "exitowner@example.com")
    await join(api.db, organization, "exitadmin@example.com", Role.ADMIN)
    member = await join(api.db, organization, "exitmember@example.com", Role.MEMBER)
    await sign_in(api, "exitadmin@example.com")

    removed = await api.client.delete(f"{ORGS}/exit-co/members/{member.id}")
    refused = await api.client.delete(f"{ORGS}/exit-co/members/{owner.id}")

    assert removed.status_code == 204, removed.text
    assert refused.status_code == 403, refused.text
    assert {m.role for m in await members_of(api, organization)} == {Role.OWNER, Role.ADMIN}
    assert member.id not in {m.user_id for m in await members_of(api, organization)}


async def test_removing_yourself_is_refused_and_points_at_leaving(api: Api) -> None:
    organization, owner = await workspace(api.db, "Stay Co", "stayowner@example.com")
    await sign_in(api, "stayowner@example.com")

    response = await api.client.delete(f"{ORGS}/stay-co/members/{owner.id}")

    assert response.status_code == 403, response.text
    assert "leave" in response.json()["message"].lower()
    assert len(await members_of(api, organization)) == 1


async def test_a_viewer_can_leave_although_they_can_remove_nobody(api: Api) -> None:
    organization, _ = await workspace(api.db, "Open Co", "openowner@example.com")
    viewer = await join(api.db, organization, "openviewer@example.com", Role.VIEWER)
    await sign_in(api, "openviewer@example.com")

    left = await api.client.delete(f"{ORGS}/open-co/members/me")
    # And the organisation is gone from their view entirely.
    after = await api.client.get(f"{ORGS}/open-co")

    assert left.status_code == 204, left.text
    assert after.status_code == 404, after.text
    assert viewer.id not in {m.user_id for m in await members_of(api, organization)}


async def test_the_last_owner_cannot_leave(api: Api) -> None:
    organization, _ = await workspace(api.db, "Anchor Co", "anchorowner@example.com")
    await join(api.db, organization, "anchoradmin@example.com", Role.ADMIN)
    await sign_in(api, "anchorowner@example.com")

    response = await api.client.delete(f"{ORGS}/anchor-co/members/me")

    assert response.status_code == 409, response.text
    assert len(await members_of(api, organization)) == 2
