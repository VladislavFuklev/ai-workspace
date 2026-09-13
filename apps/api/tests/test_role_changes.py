"""Who may change whose role, and the rules that keep an organisation usable."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.core.database import create_engine, create_session_factory
from ai_workspace_api.core.errors import ConflictError, NotFoundError, PermissionDeniedError
from ai_workspace_api.core.passwords import hash_password
from ai_workspace_api.models import Organization, Role, User
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


async def workspace(db: AsyncSession, name: str) -> tuple[Organization, User]:
    owner = await make_user(db, f"{name.lower().replace(' ', '')}-owner@example.com")
    organization = await OrganizationService(db).create(name, owner)
    return organization, owner


async def join(db: AsyncSession, organization: Organization, email: str, role: Role) -> User:
    user = await make_user(db, email)
    MembershipService(db).add_member(organization, user, role)
    await db.flush()
    return user


async def test_an_owner_can_change_a_members_role(db: AsyncSession) -> None:
    organization, owner = await workspace(db, "Change Co")
    member = await join(db, organization, "m1@example.com", Role.MEMBER)
    service = MembershipService(db)
    scope = await service.resolve_scope(owner, organization.id)

    updated = await service.change_role(scope, member.id, Role.ADMIN)

    assert updated.role is Role.ADMIN


async def test_an_admin_cannot_promote_anyone_to_owner(db: AsyncSession) -> None:
    """Without this an admin makes a second account an owner and the ladder
    means nothing."""
    organization, owner = await workspace(db, "Ladder Co")
    admin = await join(db, organization, "admin@example.com", Role.ADMIN)
    member = await join(db, organization, "m2@example.com", Role.MEMBER)
    service = MembershipService(db)
    scope = await service.resolve_scope(admin, organization.id)

    with pytest.raises(PermissionDeniedError):
        await service.change_role(scope, member.id, Role.OWNER)

    assert owner is not None  # the owner is untouched


async def test_an_admin_cannot_act_on_an_owner(db: AsyncSession) -> None:
    """The same rule from the other direction."""
    organization, owner = await workspace(db, "Upward Co")
    admin = await join(db, organization, "admin2@example.com", Role.ADMIN)
    service = MembershipService(db)
    scope = await service.resolve_scope(admin, organization.id)

    with pytest.raises(PermissionDeniedError):
        await service.change_role(scope, owner.id, Role.MEMBER)


async def test_nobody_can_change_their_own_role(db: AsyncSession) -> None:
    """Including an owner: demoting yourself by accident is how an organisation
    loses its last administrator."""
    organization, owner = await workspace(db, "Self Co")
    service = MembershipService(db)
    scope = await service.resolve_scope(owner, organization.id)

    with pytest.raises(PermissionDeniedError) as caught:
        await service.change_role(scope, owner.id, Role.MEMBER)

    assert "your own role" in str(caught.value).lower()


@pytest.mark.parametrize("role", [Role.MEMBER, Role.VIEWER])
async def test_a_member_or_viewer_cannot_change_roles(db: AsyncSession, role: Role) -> None:
    organization, _ = await workspace(db, f"Lowly {role.value} Co")
    actor = await join(db, organization, f"{role.value}-actor@example.com", role)
    target = await join(db, organization, f"{role.value}-target@example.com", Role.VIEWER)
    service = MembershipService(db)
    scope = await service.resolve_scope(actor, organization.id)

    with pytest.raises(PermissionDeniedError):
        await service.change_role(scope, target.id, Role.ADMIN)


async def test_the_last_owner_cannot_be_demoted(db: AsyncSession) -> None:
    """An organisation with no owner cannot be deleted, transferred, or have its
    billing changed by anyone."""
    organization, owner = await workspace(db, "Solo Co")
    second_owner = await join(db, organization, "second@example.com", Role.OWNER)
    service = MembershipService(db)
    scope = await service.resolve_scope(second_owner, organization.id)

    # Two owners: demoting one is fine.
    await service.change_role(scope, owner.id, Role.ADMIN)

    # Now there is one left, and they cannot be demoted by anyone.
    admin_scope = await service.resolve_scope(owner, organization.id)
    with pytest.raises(PermissionDeniedError):
        # An admin cannot act on an owner at all.
        await service.change_role(admin_scope, second_owner.id, Role.MEMBER)

    third = await join(db, organization, "third@example.com", Role.OWNER)
    third_scope = await service.resolve_scope(third, organization.id)
    await service.change_role(third_scope, second_owner.id, Role.ADMIN)

    # `third` is now the only owner and cannot demote themselves either.
    with pytest.raises(PermissionDeniedError):
        await service.change_role(third_scope, third.id, Role.ADMIN)


async def test_the_last_owner_cannot_be_removed(db: AsyncSession) -> None:
    organization, owner = await workspace(db, "Strand Co")
    second_owner = await join(db, organization, "second2@example.com", Role.OWNER)
    service = MembershipService(db)

    # With two owners, removing one is allowed.
    scope = await service.resolve_scope(second_owner, organization.id)
    await service.remove_member(scope, owner.id)

    # The remaining owner cannot remove themselves and strand the organisation.
    with pytest.raises(ConflictError) as caught:
        await service.remove_member(scope, second_owner.id)

    assert "at least one owner" in str(caught.value).lower()


async def test_an_admin_can_remove_a_member(db: AsyncSession) -> None:
    organization, _ = await workspace(db, "Remove Co")
    admin = await join(db, organization, "radmin@example.com", Role.ADMIN)
    member = await join(db, organization, "rmember@example.com", Role.MEMBER)
    service = MembershipService(db)
    scope = await service.resolve_scope(admin, organization.id)

    await service.remove_member(scope, member.id)

    remaining = await MembershipRepository(db).list_for_organization(organization.id)
    assert member.id not in {m.user_id for m in remaining}


async def test_a_member_cannot_remove_anyone(db: AsyncSession) -> None:
    organization, _ = await workspace(db, "NoRemove Co")
    actor = await join(db, organization, "nractor@example.com", Role.MEMBER)
    target = await join(db, organization, "nrtarget@example.com", Role.VIEWER)
    service = MembershipService(db)
    scope = await service.resolve_scope(actor, organization.id)

    with pytest.raises(PermissionDeniedError):
        await service.remove_member(scope, target.id)


async def test_acting_on_someone_in_another_organisation_is_not_found(
    db: AsyncSession,
) -> None:
    """The scope carries the organisation, so a user id from elsewhere simply
    is not a member here."""
    organization, owner = await workspace(db, "Here Co")
    _, elsewhere_owner = await workspace(db, "There Co")
    service = MembershipService(db)
    scope = await service.resolve_scope(owner, organization.id)

    with pytest.raises(NotFoundError):
        await service.change_role(scope, elsewhere_owner.id, Role.ADMIN)
