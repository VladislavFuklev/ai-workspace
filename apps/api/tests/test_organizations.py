"""Organisations: the tenant boundary and its uniqueness rule."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.core.database import create_engine, create_session_factory
from ai_workspace_api.core.errors import ValidationError
from ai_workspace_api.models import Organization
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


async def test_creating_an_organisation_derives_a_slug(db: AsyncSession) -> None:
    organization = await OrganizationService(db).create("Acme Legal")

    assert organization.name == "Acme Legal"
    assert organization.slug == "acme-legal"


async def test_a_ukrainian_name_gets_an_addressable_slug(db: AsyncSession) -> None:
    organization = await OrganizationService(db).create("Юридична фірма")

    assert organization.slug == "iurydychna-firma"


async def test_two_organisations_with_the_same_name_get_different_slugs(
    db: AsyncSession,
) -> None:
    """Names are not unique — two unrelated companies can both be Acme — but the
    address has to be."""
    service = OrganizationService(db)
    first = await service.create("Acme")
    second = await service.create("Acme")

    assert first.name == second.name
    assert first.slug != second.slug
    assert second.slug.startswith("acme-")


async def test_a_name_with_nothing_usable_is_refused(db: AsyncSession) -> None:
    with pytest.raises(ValidationError) as caught:
        await OrganizationService(db).create("!!! ???")

    assert caught.value.detail is not None
    assert caught.value.detail[0]["field"] == "name"


async def test_lookup_by_slug_is_case_insensitive(db: AsyncSession) -> None:
    await OrganizationService(db).create("Acme Legal")
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
