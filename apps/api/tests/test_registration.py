"""Registration, and the property that makes it safe: it says nothing."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.api.app import create_app
from ai_workspace_api.api.dependencies import get_session
from ai_workspace_api.core.database import create_engine, create_session_factory
from ai_workspace_api.core.passwords import verify_password
from ai_workspace_api.models import User
from ai_workspace_api.repositories import UserRepository

from .conftest import BuildSettings, running_app

REGISTER = "/api/v1/auth/register"
GOOD_PASSWORD = "correct horse battery staple"


def payload(email: str = "new@example.com", **overrides: object) -> dict[str, object]:
    """Overrides must be applied after the defaults, including for `email` —
    passing it positionally *and* as an override is a TypeError, not a test."""
    body: dict[str, object] = {
        "email": email,
        "password": GOOD_PASSWORD,
        "display_name": "New Person",
    }
    body.update(overrides)
    return body


# --- schema-level, no database ------------------------------------------------


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("email", "not-an-address"),
        ("email", "missing@tld"),
        ("email", ""),
        ("password", "short"),
        ("password", "password1234"),
        ("display_name", ""),
        ("display_name", "x" * 101),
    ],
)
async def test_invalid_input_is_rejected_with_a_field_error(
    settings: object, field: str, value: object
) -> None:
    """The web form maps `detail` back onto its fields (task 1.9), so the field
    name has to be there."""
    async with running_app(create_app(settings)) as client:  # type: ignore[arg-type]
        body = payload()
        body[field] = value
        response = await client.post(REGISTER, json=body)

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_failed"
    assert field in {item["field"] for item in body["detail"]}, body["detail"]


async def test_the_password_is_never_echoed(settings: object) -> None:
    async with running_app(create_app(settings)) as client:  # type: ignore[arg-type]
        response = await client.post(REGISTER, json=payload("echo@example.com", password="short"))

    assert GOOD_PASSWORD not in response.text
    assert "short" not in response.text


# --- against the database -----------------------------------------------------


@pytest.fixture
async def api(
    valid_env: dict[str, str], settings_from: BuildSettings, database_url: str
) -> AsyncIterator[tuple[httpx.AsyncClient, AsyncSession]]:
    """An app whose session is a transaction this test rolls back afterwards.

    The service commits, so without an outer transaction each test would leave
    users behind and the next run would collide on the unique index.
    """
    settings = settings_from({**valid_env, "DATABASE_URL": database_url})
    engine = create_engine(settings)
    factory = create_session_factory(engine)
    app = create_app(settings)

    connection = await engine.connect()
    transaction = await connection.begin()
    session = factory(bind=connection, join_transaction_mode="create_savepoint")

    async def override() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = override
    try:
        async with running_app(app) as client:
            yield client, session
    finally:
        app.dependency_overrides.clear()
        await session.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


@pytest.mark.integration
async def test_a_new_address_creates_a_user(
    api: tuple[httpx.AsyncClient, AsyncSession],
) -> None:
    client, session = api

    response = await client.post(REGISTER, json=payload("Fresh@Example.com"))

    assert response.status_code == 201
    user = await UserRepository(session).get_by_email("fresh@example.com")
    assert user is not None
    assert user.email == "fresh@example.com", "stored normalised whatever was sent"
    assert user.display_name == "New Person"
    assert user.is_verified is False


@pytest.mark.integration
async def test_the_stored_password_is_hashed_not_plaintext(
    api: tuple[httpx.AsyncClient, AsyncSession],
) -> None:
    client, session = api
    await client.post(REGISTER, json=payload("hashed@example.com"))

    user = await UserRepository(session).get_by_email("hashed@example.com")

    assert user is not None
    assert user.password_hash is not None
    assert GOOD_PASSWORD not in user.password_hash
    assert user.password_hash.startswith("$argon2id$")
    assert verify_password(GOOD_PASSWORD, user.password_hash) is True


@pytest.mark.integration
async def test_a_duplicate_is_indistinguishable_from_a_new_registration(
    api: tuple[httpx.AsyncClient, AsyncSession],
) -> None:
    """The point of the endpoint. A different status or body here turns any list
    of addresses into a membership test."""
    client, _ = api

    first = await client.post(REGISTER, json=payload("dupe@example.com"))
    second = await client.post(REGISTER, json=payload("dupe@example.com"))
    # Different case, so the check cannot be fooled by normalisation either.
    third = await client.post(REGISTER, json=payload("DUPE@Example.com"))

    assert first.status_code == second.status_code == third.status_code == 201
    assert first.json() == second.json() == third.json()


@pytest.mark.integration
async def test_a_duplicate_creates_nothing_and_changes_nothing(
    api: tuple[httpx.AsyncClient, AsyncSession],
) -> None:
    """Indistinguishable to the caller must not mean the second attempt did
    something — overwriting the password would be account takeover by form."""
    client, session = api
    await client.post(REGISTER, json=payload("stable@example.com"))
    original = await UserRepository(session).get_by_email("stable@example.com")
    assert original is not None
    original_hash, original_name = original.password_hash, original.display_name

    await client.post(
        REGISTER,
        json=payload(
            "stable@example.com", password="an entirely different one", display_name="Impostor"
        ),
    )

    count = await session.scalar(
        select(func.count()).select_from(User).where(User.email == "stable@example.com")
    )
    assert count == 1
    refreshed = await UserRepository(session).get_by_email("stable@example.com")
    assert refreshed is not None
    assert refreshed.password_hash == original_hash
    assert refreshed.display_name == original_name
