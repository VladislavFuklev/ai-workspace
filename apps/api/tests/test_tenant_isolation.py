"""Tenant isolation, checked against the routes that actually exist.

The isolation assertions written beside each feature cover the routes that
existed when they were written. This file covers the ones that do not exist yet:
the route list is read out of the application, so a phase-5 endpoint that takes
an id and never asks whose it is fails here on the day it is added.

Two things are asserted for every tenant-scoped route:

* a stranger gets 401 and a non-member gets 404 — the same answer as an
  organisation that is not there, with nothing in the body that says otherwise;
* the route resolves `get_tenant_scope`, so the check is structural rather than
  something each handler remembers.
"""

from __future__ import annotations

import importlib
import pkgutil
import uuid
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute

from ai_workspace_api.api.tenant_dependencies import get_tenant_scope
from ai_workspace_api.api.v1 import routes as routes_package
from ai_workspace_api.core.errors import NotFoundError
from ai_workspace_api.models import Role

from .test_organization_endpoints import Api, api, build, join, make_user, sign_in, workspace

# Re-exported so pytest resolves the fixtures, and ruff sees them used.
__all__ = ["api", "build", "join", "make_user", "sign_in", "workspace"]

pytestmark = pytest.mark.integration

SLUG_PARAMETER = "{organization_slug}"
PREFIX = "/api/v1"

# A body that satisfies every tenant-scoped route that takes one. Authorisation
# is decided before validation for these routes, so one body works for all of
# them; if that ever stops being true, the 422 says so.
ANY_BODY: dict[str, Any] = {"name": "Attempted Rename", "role": "admin"}


def tenant_routes() -> list[tuple[str, str, APIRoute]]:
    """Every (method, path, route) in v1 whose path names an organisation.

    Discovered by importing every module in `api/v1/routes` and reading its
    `router`, so a routes module added in a later phase is swept without anyone
    remembering to add it here. A list kept by hand would be the same failure
    one level up: stale, and silent about it.

    Not read from `app.routes`: FastAPI 0.141 mounts included routers lazily, so
    the app exposes them only once a request has matched. What *is* served is
    checked separately, against the OpenAPI document.
    """
    found: list[tuple[str, str, APIRoute]] = []
    for module in pkgutil.iter_modules(routes_package.__path__):
        router = getattr(
            importlib.import_module(f"{routes_package.__name__}.{module.name}"), "router", None
        )
        for route in getattr(router, "routes", []):
            if not isinstance(route, APIRoute) or SLUG_PARAMETER not in route.path:
                continue
            for method in sorted((route.methods or set()) - {"HEAD", "OPTIONS"}):
                found.append((method, PREFIX + route.path, route))
    return sorted(found, key=lambda item: (item[1], item[0]))


def served_tenant_routes(app: FastAPI) -> set[tuple[str, str]]:
    """The same question asked of the application: what does it actually serve?"""
    return {
        (method.upper(), path)
        for path, operations in app.openapi()["paths"].items()
        if SLUG_PARAMETER in path
        for method in operations
    }


def resolves(dependant: Dependant, target: object) -> bool:
    """Whether `target` appears anywhere in a route's dependency tree."""
    if dependant.call is target:
        return True
    return any(resolves(child, target) for child in dependant.dependencies)


def concrete(path: str, slug: str) -> str:
    """Fills in a route template: the tenant under test, and ids that exist nowhere."""
    filled = path.replace(SLUG_PARAMETER, slug)
    while "{" in filled:
        start = filled.index("{")
        end = filled.index("}", start)
        filled = filled[:start] + str(uuid.uuid4()) + filled[end + 1 :]
    return filled


def test_the_route_list_is_not_empty_and_matches_what_is_mounted(api: Api) -> None:
    """A broken enumerator would make every test below pass by testing nothing.

    The expected set is written out: a route added under a tenant path has to be
    acknowledged here, which is the moment to ask whether it isolates.
    """
    routes = tenant_routes()
    discovered = {(method, path) for method, path, _ in routes}

    assert len(routes) >= 7, routes
    # What the modules declare is what the application serves. A router that is
    # written but never mounted would otherwise be swept and prove nothing.
    assert discovered == served_tenant_routes(api.app)
    assert discovered == {
        ("GET", f"{PREFIX}/organizations/{SLUG_PARAMETER}"),
        ("PATCH", f"{PREFIX}/organizations/{SLUG_PARAMETER}"),
        ("DELETE", f"{PREFIX}/organizations/{SLUG_PARAMETER}"),
        ("GET", f"{PREFIX}/organizations/{SLUG_PARAMETER}/members"),
        ("DELETE", f"{PREFIX}/organizations/{SLUG_PARAMETER}/members/me"),
        ("PATCH", f"{PREFIX}/organizations/{SLUG_PARAMETER}/members/{{user_id}}"),
        ("DELETE", f"{PREFIX}/organizations/{SLUG_PARAMETER}/members/{{user_id}}"),
    }


def test_every_tenant_route_resolves_the_scope_dependency(api: Api) -> None:
    """The structural half: a new route cannot reach its handler without the
    membership being verified, whatever the handler then does."""
    missing = [
        (method, path)
        for method, path, route in tenant_routes()
        if not resolves(route.dependant, get_tenant_scope)
    ]

    assert missing == []


async def test_no_tenant_route_answers_a_stranger(api: Api) -> None:
    """Every route in one test, so a failure names all the routes that let
    someone in rather than stopping at the first."""
    answered = []
    for method, path, _ in tenant_routes():
        response = await api.client.request(method, concrete(path, "anything"), json=ANY_BODY)
        if response.status_code != 401:
            answered.append((method, path, response.status_code))

    assert answered == []


async def test_no_tenant_route_tells_a_non_member_the_organisation_exists(api: Api) -> None:
    """404 and nothing else: not the name, not the id of the organisation or of
    anyone in it, and not a different message from the one a missing
    organisation gets."""
    organization, owner = await workspace(api.db, "Cloistered Bureau", "inside@example.com")
    await make_user(api.db, "outside@example.com")
    await sign_in(api, "outside@example.com")

    leaked = []
    for method, path, _ in tenant_routes():
        response = await api.client.request(
            method, concrete(path, organization.slug), json=ANY_BODY
        )
        body = response.text
        if (
            response.status_code != 404
            or response.json()["message"] != "That workspace does not exist."
            or organization.name in body
            or str(organization.id) in body
            or str(owner.id) in body
        ):
            leaked.append((method, path, response.status_code, body))

    assert leaked == []


async def test_a_forbidden_organisation_answers_exactly_as_a_missing_one(api: Api) -> None:
    """The two must be indistinguishable, or the difference is the answer."""
    await workspace(api.db, "Cloistered Bureau", "inside2@example.com")
    await make_user(api.db, "outside2@example.com")
    await sign_in(api, "outside2@example.com")

    differing = []
    for method, path, _ in tenant_routes():
        forbidden = await api.client.request(
            method, concrete(path, "cloistered-bureau"), json=ANY_BODY
        )
        missing = await api.client.request(method, concrete(path, "no-such-bureau"), json=ANY_BODY)
        same_body = forbidden.json() | {"request_id": ""} == missing.json() | {"request_id": ""}
        if forbidden.status_code != missing.status_code or not same_body:
            differing.append((method, path, forbidden.text, missing.text))

    assert differing == []


# --- below HTTP ---------------------------------------------------------------


async def test_a_scope_from_one_organisation_cannot_read_another(api: Api) -> None:
    """The repository level, where a forgotten `WHERE` would live."""
    from ai_workspace_api.repositories import MembershipRepository
    from ai_workspace_api.services import MembershipService

    first, first_owner = await workspace(api.db, "First Bureau", "first@example.com")
    second, second_owner = await workspace(api.db, "Second Bureau", "second@example.com")

    memberships = MembershipRepository(api.db)

    assert await memberships.get(first_owner.id, second.id) is None
    assert await memberships.get(second_owner.id, first.id) is None
    assert await memberships.get_by_slug(first_owner.id, second.slug) is None

    members = await memberships.list_members_with_users(first.id)
    assert {user.id for _, user in members} == {first_owner.id}

    with pytest.raises(NotFoundError, match="does not exist"):
        await MembershipService(api.db).resolve_scope(first_owner, second.id)


async def test_a_scope_only_ever_names_its_own_organisation(api: Api) -> None:
    """Acting through a scope cannot reach another tenant even by mistake: the
    organisation is in the scope, never in the arguments."""
    from ai_workspace_api.services import MembershipService, OrganizationService

    first, first_owner = await workspace(api.db, "Alpha Bureau", "alpha@example.com")
    second, _ = await workspace(api.db, "Beta Bureau", "beta@example.com")
    join_scope = await MembershipService(api.db).resolve_scope(first_owner, first.id)

    await OrganizationService(api.db).rename(join_scope, "Alpha Renamed")

    await api.db.refresh(first)
    await api.db.refresh(second)
    assert first.name == "Alpha Renamed"
    assert second.name == "Beta Bureau"


async def test_members_of_one_organisation_are_invisible_to_the_other(api: Api) -> None:
    first, _ = await workspace(api.db, "Gamma Bureau", "gamma@example.com")
    await workspace(api.db, "Delta Bureau", "delta@example.com")
    await join(api.db, first, "gammastaff@example.com", Role.MEMBER)
    await sign_in(api, "delta@example.com")

    response = await api.client.get("/api/v1/organizations/delta-bureau/members")

    assert response.status_code == 200, response.text
    assert [member["email"] for member in response.json()] == ["delta@example.com"]
    assert "gammastaff@example.com" not in response.text
    assert str(first.id) not in response.text
