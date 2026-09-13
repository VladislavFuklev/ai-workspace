"""Organisations: the tenant boundary and its uniqueness rule."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.core.database import create_engine, create_session_factory
from ai_workspace_api.core.errors import ValidationError
from ai_workspace_api.core.passwords import hash_password
from ai_workspace_api.core.slugs import RESERVED
from ai_workspace_api.models import Organization, User
from ai_workspace_api.repositories import OrganizationRepository
from ai_workspace_api.services import OrganizationService

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


async def owner(db: AsyncSession, email: str = "owner@example.com") -> User:
    """Creating an organisation now needs someone to own it (task 4.2)."""
    user = User(
        email=email,
        password_hash=hash_password("correct horse battery staple"),
        display_name="Owner",
    )
    db.add(user)
    await db.flush()
    return user


async def test_creating_an_organisation_derives_a_slug(db: AsyncSession) -> None:
    organization = await OrganizationService(db).create("Acme Legal", await owner(db))

    assert organization.name == "Acme Legal"
    assert organization.slug == "acme-legal"


async def test_a_ukrainian_name_gets_an_addressable_slug(db: AsyncSession) -> None:
    organization = await OrganizationService(db).create("Юридична фірма", await owner(db))

    assert organization.slug == "iurydychna-firma"


async def test_two_organisations_with_the_same_name_get_different_slugs(
    db: AsyncSession,
) -> None:
    """Names are not unique — two unrelated companies can both be Acme — but the
    address has to be."""
    service = OrganizationService(db)
    creator = await owner(db)
    first = await service.create("Acme", creator)
    second = await service.create("Acme", creator)

    assert first.name == second.name
    assert first.slug != second.slug
    assert second.slug.startswith("acme-")


async def test_a_name_with_nothing_usable_is_refused(db: AsyncSession) -> None:
    with pytest.raises(ValidationError) as caught:
        await OrganizationService(db).create("!!! ???", await owner(db))

    assert caught.value.detail is not None
    assert caught.value.detail[0]["field"] == "name"


async def test_lookup_by_slug_is_case_insensitive(db: AsyncSession) -> None:
    await OrganizationService(db).create("Acme Legal", await owner(db))
    repository = OrganizationRepository(db)

    assert await repository.get_by_slug("ACME-LEGAL") is not None
    assert await repository.get_by_slug("acme-legal") is not None
    assert await repository.get_by_slug("nobody") is None


async def test_the_database_refuses_a_slug_differing_only_by_case(
    db: AsyncSession,
) -> None:
    """The service checks first; this is what makes it a guarantee. Two tenants
    that differ only by the case of their URL is not a naming quirk."""
    db.add(Organization(name="Acme", slug="acme"))
    await db.flush()

    db.add(Organization(name="Acme Two", slug="ACME"))

    with pytest.raises(IntegrityError) as caught:
        await db.flush()

    assert "uq_organizations_slug_lower" in str(caught.value)


async def test_a_name_matching_a_reserved_route_gets_a_suffixed_slug(db: AsyncSession) -> None:
    """The web app puts the slug directly under the locale, so `/en/settings`
    would be a static page rather than an organisation. Suffixing keeps the name
    usable; refusing it would tell someone their company is not allowed."""
    organization = await OrganizationService(db).create("Sign In", await owner(db))

    assert organization.name == "Sign In"
    assert organization.slug != "sign-in"
    assert organization.slug.startswith("sign-in-")


async def test_no_reserved_slug_can_be_created(db: AsyncSession) -> None:
    """One assertion per reserved word, so adding one to the set without
    handling it here fails rather than passing quietly."""
    service = OrganizationService(db)
    creator = await owner(db)

    for reserved in sorted(RESERVED):
        organization = await service.create(reserved.replace("-", " "), creator)
        assert organization.slug != reserved, reserved
