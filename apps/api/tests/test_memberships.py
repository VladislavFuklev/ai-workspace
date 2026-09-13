"""Memberships and the tenant scope — the boundary between customers."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.core.database import create_engine, create_session_factory
from ai_workspace_api.core.errors import NotFoundError
from ai_workspace_api.core.passwords import hash_password
from ai_workspace_api.core.tenancy import TenantScope
from ai_workspace_api.models import Membership, Role, User
from ai_workspace_api.repositories import MembershipRepository
from ai_workspace_api.services import MembershipService, OrganizationService

from .conftest import BuildSettings

pytestmark = pytest.mark.integration


@pytest.fixture
async def db(
    valid_env: dict[str, str], settings_from: BuildSettings, database_url: str
) -> AsyncIterator[AsyncSession]:
    engine = create_engine(settings_from({**valid_env, "DATABASE_URL": database_url}))
    factory = create_session_factory(engine)
    connection = await engine.connect()
    transaction = await connection.begin()
    session = factory(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


async def make_user(db: AsyncSession, email: str) -> User:
    user = User(
        email=email,
        password_hash=hash_password("correct horse battery staple"),
        display_name=email.split("@")[0],
    )
    db.add(user)
    await db.flush()
    return user


async def test_creating_an_organisation_makes_the_creator_its_owner(
    db: AsyncSession,
) -> None:
    """An organisation with no members is unreachable by anyone, including the
    person who just made it, and nothing in the product could fix it."""
    creator = await make_user(db, "creator@example.com")

    organization = await OrganizationService(db).create("Acme", creator)

    members = await MembershipRepository(db).list_for_organization(organization.id)
    assert len(members) == 1
    assert members[0].user_id == creator.id
    assert members[0].role is Role.OWNER


async def test_a_scope_can_be_resolved_for_a_member(db: AsyncSession) -> None:
    creator = await make_user(db, "member@example.com")
    organization = await OrganizationService(db).create("Acme", creator)

    scope = await MembershipService(db).resolve_scope(creator, organization.id)

    assert isinstance(scope, TenantScope)
    assert scope.organization_id == organization.id
    assert scope.user_id == creator.id
    assert scope.role is Role.OWNER


async def test_a_non_member_cannot_resolve_a_scope(db: AsyncSession) -> None:
    """The isolation boundary. An outsider must not obtain a scope for someone
    else's organisation, because holding one is what everything downstream
    treats as proof."""
    owner = await make_user(db, "owner@example.com")
    outsider = await make_user(db, "outsider@example.com")
    organization = await OrganizationService(db).create("Private Co", owner)

    with pytest.raises(NotFoundError):
        await MembershipService(db).resolve_scope(outsider, organization.id)


async def test_a_non_member_and_a_missing_organisation_are_indistinguishable(
    db: AsyncSession,
) -> None:
    """Saying "you are not a member" confirms the organisation exists, which
    turns a URL into a way to discover other tenants."""
    owner = await make_user(db, "owner2@example.com")
    outsider = await make_user(db, "outsider2@example.com")
    organization = await OrganizationService(db).create("Private Two", owner)
    service = MembershipService(db)

    with pytest.raises(NotFoundError) as forbidden:
        await service.resolve_scope(outsider, organization.id)
    with pytest.raises(NotFoundError) as missing:
        await service.resolve_scope(outsider, uuid.uuid4())

    assert str(forbidden.value) == str(missing.value)


async def test_a_scope_resolves_by_slug_too(db: AsyncSession) -> None:
    creator = await make_user(db, "slug@example.com")
    await OrganizationService(db).create("Acme Legal", creator)

    scope = await MembershipService(db).resolve_scope_by_slug(creator, "ACME-LEGAL")

    assert scope.role is Role.OWNER


async def test_resolving_another_tenants_slug_fails(db: AsyncSession) -> None:
    owner = await make_user(db, "slugowner@example.com")
    outsider = await make_user(db, "slugoutsider@example.com")
    await OrganizationService(db).create("Secret Corp", owner)

    with pytest.raises(NotFoundError):
        await MembershipService(db).resolve_scope_by_slug(outsider, "secret-corp")


async def test_a_user_cannot_join_the_same_organisation_twice(db: AsyncSession) -> None:
    """Two rows would mean two roles, and every permission check would have to
    decide which one wins."""
    creator = await make_user(db, "twice@example.com")
    organization = await OrganizationService(db).create("Acme", creator)

    db.add(Membership(user_id=creator.id, organization_id=organization.id, role=Role.VIEWER))

    with pytest.raises(IntegrityError) as caught:
        await db.flush()

    assert "uq_memberships_user_organization" in str(caught.value)


async def test_a_user_can_belong_to_several_organisations(db: AsyncSession) -> None:
    creator = await make_user(db, "many@example.com")
    service = OrganizationService(db)
    await service.create("First Co", creator)
    await service.create("Second Co", creator)

    memberships = await MembershipService(db).list_for_user(creator)

    assert len(memberships) == 2
    assert {organization.name for _, organization in memberships} == {"First Co", "Second Co"}


async def test_listing_shows_only_the_users_own_organisations(db: AsyncSession) -> None:
    mine = await make_user(db, "mine@example.com")
    theirs = await make_user(db, "theirs@example.com")
    service = OrganizationService(db)
    await service.create("Mine", mine)
    await service.create("Theirs", theirs)

    memberships = await MembershipService(db).list_for_user(mine)

    assert [organization.name for _, organization in memberships] == ["Mine"]


async def test_deleting_a_user_removes_the_membership(db: AsyncSession) -> None:
    """Otherwise a deleted user's row keeps granting access to an organisation."""
    creator = await make_user(db, "gone@example.com")
    organization = await OrganizationService(db).create("Acme", creator)

    await db.delete(creator)
    await db.flush()

    assert await MembershipRepository(db).list_for_organization(organization.id) == []
