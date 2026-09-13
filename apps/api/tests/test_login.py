"""Signing in, and the property that every failure looks the same."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.api.app import create_app
from ai_workspace_api.api.dependencies import get_session
from ai_workspace_api.core.database import create_engine, create_session_factory
from ai_workspace_api.core.passwords import hash_password
from ai_workspace_api.models import User
from ai_workspace_api.repositories import UserRepository

from .conftest import BuildSettings, running_app

LOGIN = "/api/v1/auth/login"
PASSWORD = "correct horse battery staple"

pytestmark = pytest.mark.integration


@pytest.fixture
async def api(
    valid_env: dict[str, str], settings_from: BuildSettings, database_url: str
) -> AsyncIterator[tuple[httpx.AsyncClient, AsyncSession]]:
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


async def seed(session: AsyncSession, email: str, **overrides: object) -> User:
    user = User(
        email=email,
        password_hash=hash_password(PASSWORD),
        display_name="Member",
        **overrides,
    )
    session.add(user)
    await session.flush()
    return user


async def test_correct_credentials_return_the_profile(
    api: tuple[httpx.AsyncClient, AsyncSession],
) -> None:
    client, session = api
    user = await seed(session, "member@example.com")

    response = await client.post(LOGIN, json={"email": "member@example.com", "password": PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "id": str(user.id),
        "email": "member@example.com",
        "display_name": "Member",
        "is_verified": False,
    }


async def test_the_response_never_carries_the_hash(
    api: tuple[httpx.AsyncClient, AsyncSession],
) -> None:
    client, session = api
    await seed(session, "nohash@example.com")

    response = await client.post(LOGIN, json={"email": "nohash@example.com", "password": PASSWORD})

    assert "password" not in response.text.lower()
    assert "argon2" not in response.text.lower()


async def test_the_address_is_case_insensitive(
    api: tuple[httpx.AsyncClient, AsyncSession],
) -> None:
    client, session = api
    await seed(session, "cased@example.com")

    response = await client.post(LOGIN, json={"email": "CASED@Example.com", "password": PASSWORD})

    assert response.status_code == 200


async def test_every_failure_is_indistinguishable(
    api: tuple[httpx.AsyncClient, AsyncSession],
) -> None:
    """The point of the endpoint. Four different facts, one answer.

    A wrong password, an unknown address, an account created through an identity
    provider, and a disabled account must not be told apart from outside.
    """
    client, session = api
    await seed(session, "real@example.com")
    await seed(session, "disabled@example.com", is_active=False)
    session.add(User(email="oauth@example.com", password_hash=None, display_name="OAuth"))
    await session.flush()

    responses = [
        await client.post(LOGIN, json={"email": "real@example.com", "password": "wrong password"}),
        await client.post(LOGIN, json={"email": "nobody@example.com", "password": PASSWORD}),
        await client.post(LOGIN, json={"email": "oauth@example.com", "password": PASSWORD}),
        await client.post(LOGIN, json={"email": "disabled@example.com", "password": PASSWORD}),
    ]

    statuses = {r.status_code for r in responses}
    bodies = {(r.json()["code"], r.json()["message"]) for r in responses}

    assert statuses == {401}, statuses
    assert len(bodies) == 1, bodies
    code, message = bodies.pop()
    assert code == "unauthenticated"

    # The message must not name *which* of the four it was. "email and password
    # do not match" is fine and is the point; "incorrect password" is not. An
    # earlier version of this test banned the word "password" outright, which
    # would have rejected a perfectly good message.
    lowered = message.lower()
    for giveaway in (
        "incorrect password",
        "wrong password",
        "invalid password",
        "no such",
        "does not exist",
        "not registered",
        "disabled",
        "inactive",
        "not found",
        "unknown user",
    ):
        assert giveaway not in lowered, f"{giveaway!r} names the cause: {message}"


async def test_an_unknown_address_costs_the_same_as_a_wrong_password(
    api: tuple[httpx.AsyncClient, AsyncSession],
) -> None:
    """Otherwise response time answers the question the body refuses to."""
    client, session = api
    await seed(session, "timed@example.com")

    async def elapsed(email: str) -> float:
        start = time.perf_counter()
        await client.post(LOGIN, json={"email": email, "password": "wrong password here"})
        return time.perf_counter() - start

    known = min([await elapsed("timed@example.com") for _ in range(3)])
    unknown = min([await elapsed("nobody@example.com") for _ in range(3)])

    # Order of magnitude, not a constant: a missing verify_absent_user makes the
    # unknown case hundreds of times faster, which is what this catches.
    assert unknown > known / 4, f"unknown={unknown:.4f}s known={known:.4f}s"


async def test_a_weak_hash_is_upgraded_on_a_successful_sign_in(
    api: tuple[httpx.AsyncClient, AsyncSession],
) -> None:
    """Cost rises with hardware without asking anyone to reset a password."""
    from argon2 import PasswordHasher

    client, session = api
    weak = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1).hash(PASSWORD)
    user = User(email="weak@example.com", password_hash=weak, display_name="Weak")
    session.add(user)
    await session.flush()

    first = await client.post(LOGIN, json={"email": "weak@example.com", "password": PASSWORD})
    assert first.status_code == 200

    refreshed = await UserRepository(session).get_by_email("weak@example.com")
    assert refreshed is not None
    assert refreshed.password_hash != weak, "the stored hash was not upgraded"

    # And the upgrade must not lock the user out.
    again = await client.post(LOGIN, json={"email": "weak@example.com", "password": PASSWORD})
    assert again.status_code == 200


async def test_a_disabled_account_cannot_sign_in_even_with_the_right_password(
    api: tuple[httpx.AsyncClient, AsyncSession],
) -> None:
    client, session = api
    await seed(session, "banned@example.com", is_active=False)

    response = await client.post(LOGIN, json={"email": "banned@example.com", "password": PASSWORD})

    assert response.status_code == 401
