"""The user table and its repository."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.core.database import create_engine, create_session_factory
from ai_workspace_api.models import Base, User
from ai_workspace_api.repositories import UserRepository, normalize_email

from .conftest import BuildSettings

USERS = Base.metadata.tables["users"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Person@Example.com", "person@example.com"),
        ("  person@example.com  ", "person@example.com"),
        ("PERSON@EXAMPLE.COM", "person@example.com"),
        ("person@example.com", "person@example.com"),
    ],
)
def test_addresses_are_normalised(raw: str, expected: str) -> None:
    assert normalize_email(raw) == expected


def test_the_password_hash_is_nullable() -> None:
    """A user created through an identity provider has no password (task 3.8).
    A sentinel value would have to be excluded everywhere a password is checked,
    and one missed check is an auth bypass."""
    assert USERS.c.password_hash.nullable is True


def test_constraints_follow_the_naming_convention() -> None:
    names = {constraint.name for constraint in USERS.constraints} | {
        index.name for index in USERS.indexes
    }

    assert "pk_users" in names
    assert "uq_users_email_lower" in names


def test_the_repr_does_not_carry_the_address() -> None:
    """A repr reaches logs and tracebacks; an address is personal data."""
    user = User(id=uuid.uuid4(), email="person@example.com", display_name="Person")

    assert "person@example.com" not in repr(user)


@pytest.fixture
async def session(
    valid_env: dict[str, str], settings_from: BuildSettings, database_url: str
) -> AsyncIterator[AsyncSession]:
    """A session whose work is rolled back, so tests cannot see each other's rows."""
    engine = create_engine(settings_from({**valid_env, "DATABASE_URL": database_url}))
    factory = create_session_factory(engine)
    async with factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()


def make_user(email: str, name: str = "Person") -> User:
    return User(email=normalize_email(email), display_name=name)


@pytest.mark.integration
async def test_a_user_can_be_stored_and_read_back(session: AsyncSession) -> None:
    repository = UserRepository(session)
    repository.add(make_user("Stored@Example.com", "Stored Person"))
    await session.flush()

    found = await repository.get_by_email("stored@example.com")

    assert found is not None
    assert found.email == "stored@example.com"
    assert found.password_hash is None
    assert found.is_active is True
    assert found.is_verified is False


@pytest.mark.integration
async def test_lookup_is_case_insensitive(session: AsyncSession) -> None:
    repository = UserRepository(session)
    repository.add(make_user("Case@Example.com"))
    await session.flush()

    assert await repository.get_by_email("CASE@EXAMPLE.COM") is not None
    assert await repository.get_by_email("  case@example.com ") is not None
    assert await repository.email_exists("Case@Example.COM") is True
    assert await repository.email_exists("other@example.com") is False


@pytest.mark.integration
async def test_the_database_refuses_a_duplicate_differing_only_by_case(
    session: AsyncSession,
) -> None:
    """The important one. The application normalises, but this is what makes it
    a guarantee — two accounts differing only by case is account takeover, not
    untidiness."""
    session.add(User(email="dupe@example.com", display_name="First"))
    await session.flush()

    # Bypassing normalize_email on purpose: this asserts the database's rule,
    # not the application's.
    session.add(User(email="DUPE@example.com", display_name="Second"))

    with pytest.raises(IntegrityError) as caught:
        await session.flush()

    assert "uq_users_email_lower" in str(caught.value)


@pytest.mark.integration
async def test_a_new_user_is_active_and_unverified(session: AsyncSession) -> None:
    """Asserted against the database, not the model: what matters is the row a
    real insert produces. Verified must default to false — defaulting it true
    would trust every account before anyone proves the address."""
    user = User(email="defaults@example.com", display_name="Defaults")
    session.add(user)
    await session.flush()
    await session.refresh(user)

    assert user.is_active is True
    assert user.is_verified is False
    assert user.created_at is not None


@pytest.mark.integration
async def test_an_unknown_address_returns_none(session: AsyncSession) -> None:
    repository = UserRepository(session)

    assert await repository.get_by_email("nobody@example.com") is None
    assert await repository.get_by_id(uuid.uuid4()) is None
