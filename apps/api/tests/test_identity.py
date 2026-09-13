"""Linking a provider identity to an account."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession as DbSession

from ai_workspace_api.core.database import create_engine, create_session_factory
from ai_workspace_api.core.errors import ConflictError
from ai_workspace_api.core.passwords import hash_password
from ai_workspace_api.models import Identity, IdentityProvider, User
from ai_workspace_api.services.identity import IdentityService, ProviderProfile

from .conftest import BuildSettings

pytestmark = pytest.mark.integration


@pytest.fixture
async def db(
    valid_env: dict[str, str], settings_from: BuildSettings, database_url: str
) -> AsyncIterator[DbSession]:
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


def profile(
    email: str = "person@example.com",
    subject: str = "provider-subject-1",
    provider: IdentityProvider = IdentityProvider.GOOGLE,
    *,
    email_verified: bool = True,
) -> ProviderProfile:
    return ProviderProfile(
        provider=provider,
        subject=subject,
        email=email,
        display_name="Provider Person",
        email_verified=email_verified,
    )


async def test_a_first_sign_in_creates_a_user_with_no_password(db: DbSession) -> None:
    user = await IdentityService(db).sign_in(profile("first@example.com"))

    assert user.password_hash is None, "an identity-provider account has no password"
    assert user.email == "first@example.com"
    assert user.is_verified is True


async def test_an_unverified_provider_email_is_not_treated_as_proven(db: DbSession) -> None:
    """Some providers do not vouch for the address; taking their word would let
    someone claim an address they do not control."""
    user = await IdentityService(db).sign_in(
        profile("unverified@example.com", email_verified=False)
    )

    assert user.is_verified is False


async def test_a_second_sign_in_returns_the_same_user(db: DbSession) -> None:
    service = IdentityService(db)
    first = await service.sign_in(profile("repeat@example.com", subject="subject-repeat"))
    second = await service.sign_in(profile("repeat@example.com", subject="subject-repeat"))

    assert first.id == second.id
    identities = (await db.execute(select(Identity))).scalars().all()
    assert len(identities) == 1


async def test_the_same_subject_under_another_provider_is_a_different_identity(
    db: DbSession,
) -> None:
    service = IdentityService(db)
    await service.sign_in(profile("google@example.com", subject="shared-id"))

    # A different provider, same subject string, different address.
    other = await service.sign_in(
        profile("github@example.com", subject="shared-id", provider=IdentityProvider.GITHUB)
    )

    identities = (await db.execute(select(Identity))).scalars().all()
    assert len(identities) == 2
    assert other.email == "github@example.com"


async def test_a_provider_email_matching_an_existing_account_is_refused(
    db: DbSession,
) -> None:
    """The case that matters. Linking automatically would mean anyone who can
    get a provider to assert an address takes over the account behind it."""
    db.add(
        User(
            email="existing@example.com",
            password_hash=hash_password("correct horse battery staple"),
            display_name="Existing",
        )
    )
    await db.flush()

    with pytest.raises(ConflictError) as caught:
        await IdentityService(db).sign_in(profile("existing@example.com", subject="new-subject"))

    assert "settings" in str(caught.value).lower(), "the message must say how to proceed"
    assert (await db.execute(select(Identity))).scalars().all() == []


async def test_a_signed_in_user_can_link_deliberately(db: DbSession) -> None:
    """What the refusal above points at: proof of the account, then the link."""
    user = User(
        email="linker@example.com",
        password_hash=hash_password("correct horse battery staple"),
        display_name="Linker",
    )
    db.add(user)
    await db.flush()

    identity = await IdentityService(db).link_to_existing(
        user, profile("linker@example.com", subject="linked-subject")
    )

    assert identity.user_id == user.id
    # And the provider now signs them into the same account.
    again = await IdentityService(db).sign_in(
        profile("linker@example.com", subject="linked-subject")
    )
    assert again.id == user.id


async def test_one_provider_account_cannot_be_linked_to_two_users(db: DbSession) -> None:
    service = IdentityService(db)
    await service.sign_in(profile("owner@example.com", subject="contested"))

    other = User(
        email="other@example.com",
        password_hash=hash_password("correct horse battery staple"),
        display_name="Other",
    )
    db.add(other)
    await db.flush()

    with pytest.raises(ConflictError):
        await service.link_to_existing(other, profile("other@example.com", subject="contested"))


async def test_the_database_refuses_a_duplicate_pair(db: DbSession) -> None:
    """The service checks first, but the constraint is what guarantees it."""
    user = await IdentityService(db).sign_in(profile("dupe@example.com", subject="dupe-subject"))

    db.add(Identity(user_id=user.id, provider=IdentityProvider.GOOGLE, subject="dupe-subject"))

    with pytest.raises(IntegrityError) as caught:
        await db.flush()

    assert "uq_identities_provider_subject" in str(caught.value)
