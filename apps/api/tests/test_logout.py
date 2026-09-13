"""Who am I, ending a session, and telling a second tab from a thief."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession as DbSession

from ai_workspace_api.api.app import create_app
from ai_workspace_api.api.cookies import ACCESS_COOKIE, REFRESH_COOKIE
from ai_workspace_api.api.dependencies import get_session
from ai_workspace_api.core.database import create_engine, create_session_factory
from ai_workspace_api.core.passwords import hash_password
from ai_workspace_api.core.settings import Settings
from ai_workspace_api.core.tokens import create_access_token, hash_refresh_token
from ai_workspace_api.models import Session, User

from .conftest import BuildSettings, running_app

LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
LOGOUT_ALL = "/api/v1/auth/logout-all"
ME = "/api/v1/auth/me"
PASSWORD = "correct horse battery staple"

pytestmark = pytest.mark.integration


@dataclass
class Api:
    """Everything a session test needs, so the fixture returns one typed thing."""

    client: httpx.AsyncClient
    db: DbSession
    settings: Settings


@asynccontextmanager
async def build_api(
    valid_env: dict[str, str],
    settings_from: BuildSettings,
    database_url: str,
    **overrides: str,
) -> AsyncIterator[Api]:
    """An app on a transaction this test rolls back afterwards."""
    settings = settings_from({**valid_env, "DATABASE_URL": database_url, **overrides})
    engine = create_engine(settings)
    factory = create_session_factory(engine)
    app = create_app(settings)

    connection = await engine.connect()
    transaction = await connection.begin()
    db = factory(bind=connection, join_transaction_mode="create_savepoint")

    async def override() -> AsyncIterator[DbSession]:
        yield db

    app.dependency_overrides[get_session] = override
    try:
        async with running_app(app) as client:
            yield Api(client=client, db=db, settings=settings)
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
    async with build_api(valid_env, settings_from, database_url) as built:
        yield built


@pytest.fixture
async def api_no_grace(
    valid_env: dict[str, str], settings_from: BuildSettings, database_url: str
) -> AsyncIterator[Api]:
    """Grace at zero: any reuse is theft, including a second tab."""
    async with build_api(
        valid_env, settings_from, database_url, REFRESH_GRACE_SECONDS="0"
    ) as built:
        yield built


async def seed(db: DbSession, email: str) -> User:
    user = User(email=email, password_hash=hash_password(PASSWORD), display_name="Member")
    db.add(user)
    await db.flush()
    return user


async def sign_in(client: httpx.AsyncClient, email: str) -> httpx.Response:
    return await client.post(LOGIN, json={"email": email, "password": PASSWORD})


async def test_me_returns_the_profile_when_signed_in(api: Api) -> None:
    client, db = api.client, api.db
    await seed(db, "me@example.com")
    await sign_in(client, "me@example.com")

    response = await client.get(ME)

    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


async def test_me_is_401_without_a_cookie(api: Api) -> None:
    client = api.client

    assert (await client.get(ME)).status_code == 401


async def test_me_is_401_with_a_tampered_token(api: Api) -> None:
    client, db = api.client, api.db
    await seed(db, "tampered@example.com")
    await sign_in(client, "tampered@example.com")
    good = client.cookies[ACCESS_COOKIE]
    header, payload, signature = good.split(".")
    client.cookies.set(ACCESS_COOKIE, f"{header}.{payload}.{signature[:-2]}xy")

    assert (await client.get(ME)).status_code == 401


async def test_me_is_401_with_an_expired_token(api: Api) -> None:
    client, db, settings = api.client, api.db, api.settings
    user = await seed(db, "stale@example.com")
    expired = create_access_token(
        user_id=user.id,
        session_id=user.id,
        secret=settings.session_secret.get_secret_value(),
        ttl_seconds=-1,
    )
    client.cookies.set(ACCESS_COOKIE, expired)

    assert (await client.get(ME)).status_code == 401


async def test_a_disabled_user_is_rejected_before_the_token_expires(api: Api) -> None:
    """Disabling an account must take effect now, not in fifteen minutes."""
    client, db = api.client, api.db
    user = await seed(db, "banned@example.com")
    await sign_in(client, "banned@example.com")
    assert (await client.get(ME)).status_code == 200

    user.is_active = False
    await db.flush()

    assert (await client.get(ME)).status_code == 401


async def test_logout_revokes_the_session_and_clears_the_cookies(api: Api) -> None:
    client, db = api.client, api.db
    await seed(db, "out@example.com")
    await sign_in(client, "out@example.com")
    refresh_token = client.cookies[REFRESH_COOKIE]

    response = await client.post(LOGOUT)

    assert response.status_code == 204
    cleared = " ".join(response.headers.get_list("set-cookie")).lower()
    assert ACCESS_COOKIE.lower() in cleared and REFRESH_COOKIE.lower() in cleared

    stored = (
        await db.execute(
            select(Session).where(Session.token_hash == hash_refresh_token(refresh_token))
        )
    ).scalar_one()
    assert stored.revoked_at is not None


async def test_the_refresh_token_stops_working_after_logout(api: Api) -> None:
    """The access token stays signature-valid until it expires (ADR-019), but
    nothing can mint a new one."""
    client, db = api.client, api.db
    await seed(db, "ended@example.com")
    await sign_in(client, "ended@example.com")
    refresh_token = client.cookies[REFRESH_COOKIE]
    await client.post(LOGOUT)

    client.cookies.set(REFRESH_COOKIE, refresh_token)

    assert (await client.post(REFRESH)).status_code == 401


async def test_logout_all_ends_sessions_from_other_sign_ins(api: Api) -> None:
    """The point: a second device the user cannot reach."""
    client, db = api.client, api.db
    user = await seed(db, "everywhere@example.com")
    await sign_in(client, "everywhere@example.com")

    # A second sign-in, as if from another device.
    second = await client.post(
        LOGIN, json={"email": "everywhere@example.com", "password": PASSWORD}
    )
    assert second.status_code == 200

    live_before = (
        (
            await db.execute(
                select(Session).where(Session.user_id == user.id, Session.revoked_at.is_(None))
            )
        )
        .scalars()
        .all()
    )
    assert len(live_before) >= 2

    assert (await client.post(LOGOUT_ALL)).status_code == 204

    live_after = (
        (
            await db.execute(
                select(Session).where(Session.user_id == user.id, Session.revoked_at.is_(None))
            )
        )
        .scalars()
        .all()
    )
    assert live_after == []


async def test_two_tabs_refreshing_at_once_are_not_treated_as_theft(api: Api) -> None:
    """Rotation makes a second tab look exactly like a replay. Within the grace
    window it is not, and neither tab gets signed out."""
    client, db = api.client, api.db
    user = await seed(db, "tabs@example.com")
    await sign_in(client, "tabs@example.com")
    shared = client.cookies[REFRESH_COOKIE]

    first = await client.post(REFRESH)
    assert first.status_code == 200

    # The second tab still holds the token the first one just retired.
    client.cookies.set(REFRESH_COOKIE, shared)
    second = await client.post(REFRESH)

    assert second.status_code == 200, "a second tab was treated as a stolen token"
    live = (
        (
            await db.execute(
                select(Session).where(Session.user_id == user.id, Session.revoked_at.is_(None))
            )
        )
        .scalars()
        .all()
    )
    assert live, "the family was revoked by a concurrent refresh"


async def test_a_replay_after_the_window_still_revokes_the_family(api: Api) -> None:
    """The grace window must not disarm reuse detection, only delay it."""
    client, db, settings = api.client, api.db, api.settings
    user = await seed(db, "late@example.com")
    await sign_in(client, "late@example.com")
    stolen = client.cookies[REFRESH_COOKIE]
    await client.post(REFRESH)

    # Age the retired token past the window rather than sleeping.
    retired = (
        await db.execute(select(Session).where(Session.token_hash == hash_refresh_token(stolen)))
    ).scalar_one()
    grace = settings.refresh_grace_seconds
    retired.revoked_at = datetime.now(UTC) - timedelta(seconds=grace + 5)
    await db.flush()

    client.cookies.set(REFRESH_COOKIE, stolen)
    assert (await client.post(REFRESH)).status_code == 401

    live = (
        (
            await db.execute(
                select(Session).where(Session.user_id == user.id, Session.revoked_at.is_(None))
            )
        )
        .scalars()
        .all()
    )
    assert live == []


async def test_the_window_can_be_switched_off(api_no_grace: Api) -> None:
    """With the grace at zero, any reuse is theft — including a second tab."""
    client, db = api_no_grace.client, api_no_grace.db
    await seed(db, "strict@example.com")
    await sign_in(client, "strict@example.com")
    shared = client.cookies[REFRESH_COOKIE]
    await client.post(REFRESH)

    client.cookies.set(REFRESH_COOKIE, shared)

    assert (await client.post(REFRESH)).status_code == 401
