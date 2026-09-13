"""Session tokens: cookies, rotation, and what happens when one is replayed."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import httpx
import jwt
import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession as DbSession

from ai_workspace_api.api.app import create_app
from ai_workspace_api.api.cookies import ACCESS_COOKIE, REFRESH_COOKIE
from ai_workspace_api.api.dependencies import get_session
from ai_workspace_api.core.database import create_engine, create_session_factory
from ai_workspace_api.core.passwords import hash_password
from ai_workspace_api.core.tokens import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_refresh_token,
)
from ai_workspace_api.models import Session, User

from .conftest import BuildSettings, running_app

LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
PASSWORD = "correct horse battery staple"
# 32+ bytes, matching what the setting requires and RFC 7518 recommends.
SECRET = "a-test-signing-secret-of-sufficient-length"


# --- token primitives, no database -------------------------------------------


def test_an_access_token_round_trips() -> None:
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    token = create_access_token(
        user_id=user_id, session_id=session_id, secret=SECRET, ttl_seconds=60
    )

    assert decode_access_token(token, secret=SECRET) == (user_id, session_id)


def test_a_token_signed_with_another_key_is_rejected() -> None:
    token = create_access_token(
        user_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        secret="a-different-signing-key-also-long-enough",
        ttl_seconds=60,
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(token, secret=SECRET)


def test_a_tampered_token_is_rejected() -> None:
    token = create_access_token(
        user_id=uuid.uuid4(), session_id=uuid.uuid4(), secret=SECRET, ttl_seconds=60
    )
    header, payload, signature = token.split(".")

    with pytest.raises(InvalidTokenError):
        decode_access_token(f"{header}.{payload}x.{signature}", secret=SECRET)


def test_an_expired_token_is_rejected() -> None:
    token = create_access_token(
        user_id=uuid.uuid4(), session_id=uuid.uuid4(), secret=SECRET, ttl_seconds=-1
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(token, secret=SECRET)


def test_an_unsigned_token_is_rejected() -> None:
    """`alg: none` is the classic JWT forgery; pinning the algorithm stops it."""
    forged = jwt.encode({"sub": str(uuid.uuid4()), "typ": "access"}, key="", algorithm="none")

    with pytest.raises(InvalidTokenError):
        decode_access_token(forged, secret=SECRET)


def test_a_token_of_the_wrong_kind_is_rejected() -> None:
    """Otherwise a token minted for one purpose works for another."""
    other = jwt.encode(
        {"sub": str(uuid.uuid4()), "sid": str(uuid.uuid4()), "typ": "reset"},
        SECRET,
        algorithm="HS256",
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(other, secret=SECRET)


def test_the_token_carries_nothing_but_identifiers() -> None:
    """A JWT is base64, not encryption: anything in it is readable."""
    token = create_access_token(
        user_id=uuid.uuid4(), session_id=uuid.uuid4(), secret=SECRET, ttl_seconds=60
    )
    claims = jwt.decode(token, SECRET, algorithms=["HS256"])

    assert set(claims) == {"sub", "sid", "typ", "iat", "exp"}


def test_insecure_cookies_are_refused_in_production(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    with pytest.raises(ValidationError) as caught:
        settings_from({**valid_env, "ENVIRONMENT": "production", "COOKIE_SECURE": "false"})

    assert "cookie_secure" in str(caught.value)


def test_a_missing_session_secret_is_refused(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    """A signing key with a fallback is one somebody forgot to set."""
    without = {k: v for k, v in valid_env.items() if k != "SESSION_SECRET"}

    with pytest.raises(ValidationError) as caught:
        settings_from(without)

    assert "session_secret" in str(caught.value).lower()


# --- against the database -----------------------------------------------------


@pytest.fixture
async def api(
    valid_env: dict[str, str], settings_from: BuildSettings, database_url: str
) -> AsyncIterator[tuple[httpx.AsyncClient, DbSession]]:
    settings = settings_from({**valid_env, "DATABASE_URL": database_url})
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
            yield client, db
    finally:
        app.dependency_overrides.clear()
        await db.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


async def seed(db: DbSession, email: str) -> User:
    user = User(email=email, password_hash=hash_password(PASSWORD), display_name="Member")
    db.add(user)
    await db.flush()
    return user


async def sign_in(client: httpx.AsyncClient, email: str) -> httpx.Response:
    return await client.post(LOGIN, json={"email": email, "password": PASSWORD})


pytestmark_integration = pytest.mark.integration


@pytest.mark.integration
async def test_signing_in_sets_both_cookies_with_safe_flags(
    api: tuple[httpx.AsyncClient, DbSession],
) -> None:
    client, db = api
    await seed(db, "cookies@example.com")

    response = await sign_in(client, "cookies@example.com")

    assert response.status_code == 200
    jar = {c.split("=")[0]: c for c in response.headers.get_list("set-cookie")}
    assert ACCESS_COOKIE in jar and REFRESH_COOKIE in jar

    for name, raw in jar.items():
        lowered = raw.lower()
        assert "httponly" in lowered, f"{name} is readable by script"
        assert "samesite=lax" in lowered, f"{name} has no SameSite"

    # The refresh cookie must not ride along on every request.
    assert "path=/api/v1/auth/refresh" in jar[REFRESH_COOKIE].lower()
    assert "path=/;" in jar[ACCESS_COOKIE].lower() + ";"


@pytest.mark.integration
async def test_the_raw_refresh_token_is_not_stored(
    api: tuple[httpx.AsyncClient, DbSession],
) -> None:
    """A database leak must not hand out live sessions."""
    client, db = api
    await seed(db, "hashed@example.com")
    await sign_in(client, "hashed@example.com")

    raw = client.cookies[REFRESH_COOKIE]
    stored = (await db.execute(select(Session))).scalars().all()

    assert len(stored) == 1
    assert stored[0].token_hash != raw
    assert stored[0].token_hash == hash_refresh_token(raw)


@pytest.mark.integration
async def test_refreshing_issues_a_new_pair_and_retires_the_old(
    api: tuple[httpx.AsyncClient, DbSession],
) -> None:
    client, db = api
    await seed(db, "rotate@example.com")
    await sign_in(client, "rotate@example.com")
    first_refresh = client.cookies[REFRESH_COOKIE]

    response = await client.post(REFRESH)

    assert response.status_code == 200
    second_refresh = client.cookies[REFRESH_COOKIE]
    assert second_refresh != first_refresh

    retired = (
        await db.execute(
            select(Session).where(Session.token_hash == hash_refresh_token(first_refresh))
        )
    ).scalar_one()
    assert retired.revoked_at is not None


@pytest.mark.integration
async def test_replaying_a_retired_token_revokes_the_whole_family(
    api: tuple[httpx.AsyncClient, DbSession],
) -> None:
    """The point of rotation. A stolen token works once; the moment either party
    uses the retired one, both are signed out — loudly, on purpose.

    The retired token is aged past the grace window added in 3.6, which exists so
    a second browser tab is not mistaken for a thief. Without that, this test
    exercises the concurrent-refresh path instead of the one it is about.
    """
    client, db = api
    await seed(db, "replay@example.com")
    await sign_in(client, "replay@example.com")
    stolen = client.cookies[REFRESH_COOKIE]

    await client.post(REFRESH)  # legitimate rotation retires `stolen`
    assert (await client.post(REFRESH)).status_code == 200  # current token still fine

    retired = (
        await db.execute(select(Session).where(Session.token_hash == hash_refresh_token(stolen)))
    ).scalar_one()
    retired.revoked_at = datetime.now(UTC) - timedelta(minutes=5)
    await db.flush()

    # The thief replays the retired token. Set on the jar rather than passed per
    # request: httpx deprecated per-request cookies because what happens to the
    # jar afterwards is ambiguous.
    client.cookies.set(REFRESH_COOKIE, stolen)
    replay = await client.post(REFRESH)
    assert replay.status_code == 401

    live = (await db.execute(select(Session).where(Session.revoked_at.is_(None)))).scalars().all()
    assert live == [], "the family survived a detected replay"


@pytest.mark.integration
async def test_an_unknown_refresh_token_is_rejected(
    api: tuple[httpx.AsyncClient, DbSession],
) -> None:
    client, _ = api

    client.cookies.set(REFRESH_COOKIE, "not-a-real-token")
    response = await client.post(REFRESH)

    assert response.status_code == 401


@pytest.mark.integration
async def test_a_missing_refresh_cookie_is_rejected(
    api: tuple[httpx.AsyncClient, DbSession],
) -> None:
    client, _ = api

    assert (await client.post(REFRESH)).status_code == 401


@pytest.mark.integration
async def test_an_expired_session_cannot_refresh(
    api: tuple[httpx.AsyncClient, DbSession],
) -> None:
    client, db = api
    user = await seed(db, "expired@example.com")
    await sign_in(client, "expired@example.com")

    stored = (await db.execute(select(Session).where(Session.user_id == user.id))).scalar_one()
    stored.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await db.flush()

    assert (await client.post(REFRESH)).status_code == 401


@pytest.mark.integration
async def test_a_disabled_user_cannot_refresh(
    api: tuple[httpx.AsyncClient, DbSession],
) -> None:
    """Disabling an account must end it, not wait for the refresh token to expire."""
    client, db = api
    user = await seed(db, "disabled@example.com")
    await sign_in(client, "disabled@example.com")

    user.is_active = False
    await db.flush()

    assert (await client.post(REFRESH)).status_code == 401
