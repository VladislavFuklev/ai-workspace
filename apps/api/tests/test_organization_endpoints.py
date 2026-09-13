"""Organisation endpoints — and who each one refuses."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Annotated

import httpx
import pytest
from fastapi import APIRouter, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.api.app import create_app
from ai_workspace_api.api.dependencies import get_session
from ai_workspace_api.api.tenant_dependencies import require_permission
from ai_workspace_api.core.database import create_engine, create_session_factory
from ai_workspace_api.core.passwords import hash_password
from ai_workspace_api.core.permissions import Permission
from ai_workspace_api.core.settings import Settings
from ai_workspace_api.core.tenancy import TenantScope
from ai_workspace_api.models import Organization, Role, User
from ai_workspace_api.services import MembershipService, OrganizationService

from .conftest import BuildSettings, running_app

ORGS = "/api/v1/organizations"
PASSWORD = "correct horse battery staple"

pytestmark = pytest.mark.integration


@dataclass
class Api:
    client: httpx.AsyncClient
    db: AsyncSession
    settings: Settings
    app: FastAPI


@asynccontextmanager
async def build(
    valid_env: dict[str, str], settings_from: BuildSettings, database_url: str
) -> AsyncIterator[Api]:
    settings = settings_from({**valid_env, "DATABASE_URL": database_url})
    engine = create_engine(settings)
    factory = create_session_factory(engine)
    app = create_app(settings)
    connection = await engine.connect()
    transaction = await connection.begin()
    db = factory(bind=connection, join_transaction_mode="create_savepoint")

    async def override() -> AsyncIterator[AsyncSession]:
        yield db

    app.dependency_overrides[get_session] = override
    try:
        async with running_app(app) as client:
            yield Api(client=client, db=db, settings=settings, app=app)
    finally:
        app.dependency_overrides.clear()
        await db.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


@pytest.fixture
async def api(
    valid_env: dict[str, str], settings_from: BuildSettings, database_url: str
) -> AsyncIterator[Api]:
    async with build(valid_env, settings_from, database_url) as built:
        yield built


async def make_user(db: AsyncSession, email: str) -> User:
    user = User(
        email=email, password_hash=hash_password(PASSWORD), display_name=email.split("@")[0]
    )
    db.add(user)
    await db.flush()
    return user


async def sign_in(api: Api, email: str) -> None:
    response = await api.client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert response.status_code == 200, response.text


async def workspace(db: AsyncSession, name: str, owner_email: str) -> tuple[Organization, User]:
    owner = await make_user(db, owner_email)
    organization = await OrganizationService(db).create(name, owner)
    return organization, owner


async def join(db: AsyncSession, org: Organization, email: str, role: Role) -> User:
    user = await make_user(db, email)
    MembershipService(db).add_member(org, user, role)
    await db.flush()
    return user


# --- authentication -----------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", ORGS),
        ("POST", ORGS),
        ("GET", f"{ORGS}/anything"),
        ("GET", f"{ORGS}/anything/members"),
    ],
)
async def test_every_endpoint_refuses_a_signed_out_caller(api: Api, method: str, path: str) -> None:
    response = await api.client.request(method, path, json={"name": "Acme"})

    assert response.status_code == 401, response.text


# --- creating and listing -----------------------------------------------------


async def test_creating_an_organisation_returns_it_and_makes_the_caller_owner(
    api: Api,
) -> None:
    await make_user(api.db, "creator@example.com")
    await sign_in(api, "creator@example.com")

    response = await api.client.post(ORGS, json={"name": "Acme Legal"})

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["slug"] == "acme-legal"
    assert body["role"] == "owner"


async def test_listing_returns_only_your_own_organisations(api: Api) -> None:
    """There is no endpoint that lists all of them, and this one must not become
    it by accident."""
    mine = await make_user(api.db, "mine@example.com")
    await OrganizationService(api.db).create("Mine Co", mine)
    theirs = await make_user(api.db, "theirs@example.com")
    await OrganizationService(api.db).create("Theirs Co", theirs)
    await sign_in(api, "mine@example.com")

    response = await api.client.get(ORGS)

    assert response.status_code == 200
    assert [row["name"] for row in response.json()] == ["Mine Co"]


# --- the tenant boundary ------------------------------------------------------


async def test_a_non_member_gets_the_same_answer_as_a_missing_organisation(
    api: Api,
) -> None:
    """The boundary. A different status for "exists but not yours" turns a URL
    into a way to discover other customers."""
    await workspace(api.db, "Private Co", "owner@example.com")
    await make_user(api.db, "outsider@example.com")
    await sign_in(api, "outsider@example.com")

    forbidden = await api.client.get(f"{ORGS}/private-co")
    missing = await api.client.get(f"{ORGS}/no-such-workspace")

    assert forbidden.status_code == missing.status_code == 404
    assert forbidden.json()["code"] == missing.json()["code"]
    assert forbidden.json()["message"] == missing.json()["message"]


async def test_a_member_can_read_their_own_organisation(api: Api) -> None:
    organization, _ = await workspace(api.db, "Open Co", "openowner@example.com")
    await join(api.db, organization, "viewer@example.com", Role.VIEWER)
    await sign_in(api, "viewer@example.com")

    response = await api.client.get(f"{ORGS}/open-co")

    assert response.status_code == 200
    assert response.json()["role"] == "viewer"


async def test_members_are_listed_with_their_roles(api: Api) -> None:
    organization, owner = await workspace(api.db, "Team Co", "teamowner@example.com")
    await join(api.db, organization, "teammember@example.com", Role.MEMBER)
    await sign_in(api, "teamowner@example.com")

    response = await api.client.get(f"{ORGS}/team-co/members")

    assert response.status_code == 200
    by_email = {row["email"]: row["role"] for row in response.json()}
    assert by_email == {"teamowner@example.com": "owner", "teammember@example.com": "member"}
    assert owner is not None


async def test_a_non_member_cannot_list_members(api: Api) -> None:
    await workspace(api.db, "Closed Co", "closedowner@example.com")
    await make_user(api.db, "nosy@example.com")
    await sign_in(api, "nosy@example.com")

    response = await api.client.get(f"{ORGS}/closed-co/members")

    assert response.status_code == 404, "a non-member must not learn it exists"


async def test_a_malformed_slug_is_rejected_before_any_lookup(api: Api) -> None:
    """The path pattern refuses shapes a slug can never have, so a malformed one
    never reaches a query."""
    await make_user(api.db, "shape@example.com")
    await sign_in(api, "shape@example.com")

    response = await api.client.get(f"{ORGS}/Not%20A%20Slug")

    assert response.status_code == 422


# A route needing a permission viewers lack. Every real endpoint so far needs
# only permissions every role has, so without this the 403 path would go
# untested until 4.6 mounts something restricted.
guarded = APIRouter()


@guarded.get("/organizations/{organization_slug}/danger")
async def danger(
    scope: Annotated[TenantScope, require_permission(Permission.ORGANIZATION_DELETE)],
) -> dict[str, str]:
    return {"role": scope.role.value}


async def test_the_permission_dependency_refuses_a_viewer_and_names_what_is_missing(
    api: Api,
) -> None:
    """403 rather than 404: the caller has already proved they belong here, so
    naming the permission leaks nothing and tells them what to ask an
    administrator for."""
    api.app.include_router(guarded, prefix="/api/v1")
    organization, _ = await workspace(api.db, "Guarded Co", "guardowner@example.com")
    await join(api.db, organization, "guardviewer@example.com", Role.VIEWER)

    await sign_in(api, "guardviewer@example.com")
    refused = await api.client.get(f"{ORGS}/guarded-co/danger")

    await sign_in(api, "guardowner@example.com")
    allowed = await api.client.get(f"{ORGS}/guarded-co/danger")

    assert refused.status_code == 403, refused.text
    assert "organization:delete" in refused.json()["message"]
    assert allowed.status_code == 200
    assert allowed.json()["role"] == "owner"
